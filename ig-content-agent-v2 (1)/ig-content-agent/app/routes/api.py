from __future__ import annotations

import csv
import io
import json
import queue
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, Response, current_app, g, jsonify, request, send_file, stream_with_context

from ..db import parse_iso
from ..llm import LLMError
from ..media import MediaError, safe_child
from ..security import client_ip, login_required
from ..services import ServiceError

bp = Blueprint("api", __name__, url_prefix="/api")

MIME = {".mp4": "video/mp4", ".mov": "video/quicktime", ".m4v": "video/mp4", ".webm": "video/webm", ".gif": "image/gif",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


def C():
    return current_app.extensions["ctx"]


def body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def limited(bucket: str, limit: int, window: int = 60):
    if not C().limiter.hit(bucket, client_ip(), limit, window):
        raise ServiceError("Too many requests. Wait a moment and try again.", 429)


@bp.errorhandler(ServiceError)
def _service_error(e):
    return jsonify(error=e.message), e.status


@bp.errorhandler(MediaError)
def _media_error(e):
    return jsonify(error=str(e)), 400


@bp.errorhandler(LLMError)
def _llm_error(e):
    return jsonify(error=str(e)), 502


def _age(ts: str):
    if not ts:
        return None
    return max(0, int((datetime.now(timezone.utc) - parse_iso(ts)).total_seconds()))


@bp.get("/state")
@login_required
def state():
    c, s = C(), C().settings
    ages = {k: _age(c.db.kv_get(f"heartbeat:{k}")) for k in ("media", "publish", "watcher")}
    alive = all(a is not None and a < 30 for a in ages.values())
    return jsonify(
        counts=c.posts.counts(g.owner_id), workers=ages, workers_alive=alive,
        settings={"dry_run": s.dry_run, "ig_connected": s.ig_configured, "llm": c.llm.name if c.llm else "offline",
                  "public_media": bool(s.public_media_base_url), "local_tts": s.local_tts,
                  "local_tts_available": c.notifier.local_tts_available, "telegram": bool(s.telegram_bot_token and s.telegram_chat_id),
                  "ffmpeg": c.ff.available, "max_upload_mb": s.max_upload_mb, "inbox_dir": str(s.inbox_dir),
                  "brand_name": s.brand_name},
        pending_jobs=c.db.one("SELECT COUNT(*) c FROM jobs WHERE status IN ('queued','running')")["c"])


# ---- posts ---------------------------------------------------------------------------------------
@bp.get("/posts")
@login_required
def posts_list():
    return jsonify(posts=C().posts.list(g.owner_id))


@bp.post("/posts")
@login_required
def posts_create():
    limited("create", 30)
    d = body()
    c = C()
    pid = c.posts.create(g.owner_id, title=d.get("title", ""), brief=d.get("brief", ""), media_type=str(d.get("media_type", "REEL")).upper(),
                         auto_render=bool(d.get("auto_render")), caption=d.get("caption", ""), hashtags=d.get("hashtags", ""))
    return jsonify(c.posts.get(g.owner_id, pid)), 201


@bp.get("/posts/<int:pid>")
@login_required
def post_get(pid):
    return jsonify(C().posts.get(g.owner_id, pid))


@bp.patch("/posts/<int:pid>")
@login_required
def post_update(pid):
    return jsonify(C().posts.update(g.owner_id, pid, body()))


@bp.delete("/posts/<int:pid>")
@login_required
def post_delete(pid):
    C().posts.archive(g.owner_id, pid)
    return jsonify(ok=True)


@bp.post("/posts/<int:pid>/assets")
@login_required
def post_upload(pid):
    limited("upload", 30)
    c = C()
    files = [f for f in request.files.getlist("file") if f and f.filename]
    if not files:
        raise ServiceError("Choose a file to upload.")
    if len(files) > 10:
        raise ServiceError("Upload at most 10 files at a time.")
    for f in files:
        c.media.save_upload(g.owner_id, pid, f)
    return jsonify(c.posts.get(g.owner_id, pid)), 201


@bp.post("/posts/<int:pid>/approve")
@login_required
def post_approve(pid):
    return jsonify(C().posts.approve(g.owner_id, pid))


@bp.post("/posts/<int:pid>/send-back")
@login_required
def post_send_back(pid):
    return jsonify(C().posts.send_back(g.owner_id, pid))


@bp.post("/posts/<int:pid>/reject")
@login_required
def post_reject(pid):
    return jsonify(C().posts.reject(g.owner_id, pid))


@bp.post("/posts/<int:pid>/publish")
@login_required
def post_publish(pid):
    """Approve (if needed) and publish. This is a deliberate click on the exact post the owner is looking at."""
    c = C()
    d = body()
    post = c.posts.row(g.owner_id, pid)
    if post["state"] == "READY_FOR_REVIEW":
        c.posts.approve(g.owner_id, pid)
    return jsonify(c.posts.request_publish(g.owner_id, pid))


@bp.post("/posts/<int:pid>/regenerate")
@login_required
def post_regenerate(pid):
    limited("regen", 20)
    c = C()
    post = c.posts.row(g.owner_id, pid)
    if not (post["brief"] or post["title"]):
        raise ServiceError("Add a title or brief first so there is something to write about.")
    c.jobs.enqueue(g.owner_id, "generate_content", pid, {"force": True, "auto_render": False})
    c.posts.refresh_state(pid)
    return jsonify(c.posts.get(g.owner_id, pid))


@bp.post("/posts/<int:pid>/render-text")
@login_required
def post_render_text(pid):
    limited("render", 20)
    c = C()
    post = c.posts.row(g.owner_id, pid)
    text = str(body().get("text") or post["brief"] or post["caption"] or post["title"]).strip()[:2000]
    if not text:
        raise ServiceError("Write a brief or caption first so there is text to put on screen.")
    c.jobs.enqueue(g.owner_id, "render_template", pid, {"text": text})
    c.posts.refresh_state(pid)
    return jsonify(c.posts.get(g.owner_id, pid))


@bp.post("/posts/<int:pid>/reprocess")
@login_required
def post_reprocess(pid):
    c = C()
    c.posts.row(g.owner_id, pid)
    for a in c.posts.assets(pid):
        if a["storage_key"] != a["ready_key"]:
            c.db.execute("UPDATE assets SET status='raw' WHERE id=?", (a["id"],))
            c.jobs.enqueue(g.owner_id, "normalize", pid, {"asset_id": a["id"]})
    c.posts.refresh_state(pid)
    return jsonify(c.posts.get(g.owner_id, pid))


@bp.get("/posts/<int:pid>/media/<int:aid>")
@login_required
def post_media(pid, aid):
    c = C()
    c.posts.row(g.owner_id, pid)
    a = c.db.one("SELECT * FROM assets WHERE id=? AND post_id=? AND owner_id=?", (aid, pid, g.owner_id))
    if not a:
        raise ServiceError("File not found.", 404)
    path = c.media.path_of(a, ready=True)
    if not path.exists():
        raise ServiceError("File not found.", 404)
    resp = send_file(path, mimetype=MIME.get(path.suffix.lower(), "application/octet-stream"), conditional=True)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Cache-Control"] = "private, max-age=60"
    return resp


# ---- live events ---------------------------------------------------------------------------------
def _sse(event: str, data: dict, id_=None) -> str:
    head = f"id: {id_}\n" if id_ else ""
    return f"{head}event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@bp.get("/events")
@login_required
def events():
    c = C()
    if c.bus.subscriber_count >= 12:
        raise ServiceError("Too many live connections. Close another tab.", 429)
    owner = g.owner_id
    last = request.headers.get("Last-Event-ID") or request.args.get("after") or "0"
    after = int(last) if last.isdigit() else 0
    q = c.bus.subscribe()

    def gen():
        try:
            yield "retry: 3000\n\n"
            for a in c.activity.since(owner, after, 100):
                yield _sse("activity", a, a["id"])
            yield _sse("hello", {"ok": True})
            while True:
                try:
                    o, t, d = q.get(timeout=15)
                except queue.Empty:
                    yield ": ping\n\n"
                    continue
                if o == owner:
                    yield _sse(t, d, d.get("id") if t == "activity" else None)
        finally:
            c.bus.unsubscribe(q)

    return Response(stream_with_context(gen()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no", "Connection": "keep-alive"})


@bp.get("/activity")
@login_required
def activity():
    return jsonify(activity=C().activity.recent(g.owner_id, 80))


@bp.get("/activity/export")
@login_required
def activity_export():
    rows = C().db.all("SELECT id, created_at, level, permission_level, post_id, message FROM activity WHERE owner_id=? ORDER BY id",
                      (g.owner_id,))
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "time_utc", "level", "permission", "post_id", "message"])
    for r in rows:
        w.writerow([r["id"], r["created_at"], r["level"], r["permission_level"], r["post_id"] or "",
                    ("'" + r["message"]) if r["message"][:1] in "=+-@" else r["message"]])  # stop spreadsheet formula injection
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=activity-log.csv"})


# ---- assistant -----------------------------------------------------------------------------------
@bp.get("/briefing")
@login_required
def briefing():
    return jsonify(text=C().assistant.briefing(g.owner_id))


@bp.get("/assistant/history")
@login_required
def assistant_history():
    return jsonify(messages=C().assistant.history(g.owner_id))


@bp.post("/assistant")
@login_required
def assistant_message():
    limited("assistant", 40)
    return jsonify(C().assistant.handle(g.owner_id, str(body().get("message") or "")))


@bp.post("/assistant/confirm")
@login_required
def assistant_confirm():
    limited("confirm", 20)
    return jsonify(C().assistant.confirm(g.owner_id, str(body().get("token") or "")))
