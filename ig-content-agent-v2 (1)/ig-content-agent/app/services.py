"""Posts, approvals and the job queue. The post state machine lives here."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

from .db import Database, now_iso, parse_iso
from .events import ActivityLog, EventBus
from .media import Ffmpeg, MediaError, spec_checks

MEDIA_TYPES = ("REEL", "IMAGE", "CAROUSEL", "STORY")
LOCKED = {"PUBLISHING", "PUBLISHED", "ARCHIVED"}
BOARD_STATES = ("DRAFT", "RENDERING", "READY_FOR_REVIEW", "APPROVED", "PUBLISHING", "PUBLISHED",
                "DRY_RUN_COMPLETE", "REJECTED", "FAILED")
MAX_CAPTION = 2200
MAX_HASHTAGS = 30


class ServiceError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def clean_text(value, field: str, max_len: int, required: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ServiceError(f"{field} must be text.")
    value = value.replace("\x00", "").strip()
    if required and not value:
        raise ServiceError(f"{field} is required.")
    if len(value) > max_len:
        raise ServiceError(f"{field} is too long ({len(value)} of {max_len} characters).")
    return value


def clean_hashtags(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(v) for v in value)
    if not isinstance(value, str):
        raise ServiceError("Hashtags must be text.")
    seen, out = set(), []
    for tok in re.split(r"[\s,]+", value):
        tok = tok.strip().lstrip("#")
        if not tok:
            continue
        if not re.fullmatch(r"\w{1,100}", tok):
            raise ServiceError(f"'{tok[:20]}' is not a valid hashtag. Use letters, numbers and underscores only.")
        if tok.lower() not in seen:
            seen.add(tok.lower())
            out.append("#" + tok)
    if len(out) > MAX_HASHTAGS:
        raise ServiceError(f"Instagram allows at most {MAX_HASHTAGS} hashtags.")
    return " ".join(out)


def caption_full(post) -> str:
    cap, tags = (post["caption"] or "").strip(), (post["hashtags"] or "").strip()
    return cap + (("\n\n" + tags) if tags else "")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class JobQueue:
    def __init__(self, db: Database):
        self.db = db

    def enqueue(self, owner_id: int, kind: str, post_id: int | None = None, payload: dict | None = None,
                run_at: str | None = None, dedupe: bool = True) -> int | None:
        payload = payload or {}
        if dedupe:
            row = self.db.one("SELECT id FROM jobs WHERE owner_id=? AND kind=? AND IFNULL(post_id,0)=? AND status IN ('queued','running') "
                              "AND payload_json=?", (owner_id, kind, post_id or 0, json.dumps(payload, sort_keys=True)))
            if row:
                return None
        ts = now_iso()
        cur = self.db.execute(
            "INSERT INTO jobs(owner_id,post_id,kind,payload_json,status,run_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (owner_id, post_id, kind, json.dumps(payload, sort_keys=True), "queued", run_at or ts, ts, ts))
        return cur.lastrowid

    def claim(self, kinds: tuple):
        marks = ",".join("?" * len(kinds))
        with self.db.tx() as c:
            row = c.execute(f"SELECT * FROM jobs WHERE status='queued' AND run_at<=? AND kind IN ({marks}) "
                            "ORDER BY id LIMIT 1", (now_iso(), *kinds)).fetchone()
            if not row:
                return None
            c.execute("UPDATE jobs SET status='running', attempts=attempts+1, updated_at=? WHERE id=?", (now_iso(), row["id"]))
        return self.db.one("SELECT * FROM jobs WHERE id=?", (row["id"],))

    def finish(self, job_id: int) -> None:
        self.db.execute("UPDATE jobs SET status='done', updated_at=? WHERE id=?", (now_iso(), job_id))

    def fail(self, job_id: int, error: str) -> None:
        self.db.execute("UPDATE jobs SET status='failed', error=?, updated_at=? WHERE id=?", (error[:300], now_iso(), job_id))

    def retry_later(self, job_id: int, run_at: str, error: str) -> None:
        self.db.execute("UPDATE jobs SET status='queued', run_at=?, error=?, updated_at=? WHERE id=?",
                        (run_at, error[:300], now_iso(), job_id))

    def recover_stuck(self) -> int:
        """After a crash or restart, running jobs go back to the queue."""
        cur = self.db.execute("UPDATE jobs SET status='queued', updated_at=? WHERE status='running'", (now_iso(),))
        return cur.rowcount

    def active_for_post(self, post_id: int) -> list:
        return self.db.all("SELECT kind,status FROM jobs WHERE post_id=? AND status IN ('queued','running')", (post_id,))


class PostService:
    def __init__(self, db: Database, settings, bus: EventBus, activity: ActivityLog, jobs: JobQueue, notifier):
        self.db, self.s, self.bus, self.activity, self.jobs, self.notifier = db, settings, bus, activity, jobs, notifier

    # ---- reads ------------------------------------------------------------------------------------
    def row(self, owner_id: int, post_id: int):
        r = self.db.one("SELECT * FROM posts WHERE id=? AND owner_id=? AND state!='ARCHIVED'", (post_id, owner_id))
        if not r:
            raise ServiceError("Post not found.", 404)
        return r

    def assets(self, post_id: int) -> list:
        return self.db.all("SELECT * FROM assets WHERE post_id=? ORDER BY position, id", (post_id,))

    def list(self, owner_id: int, limit: int = 200) -> list:
        rows = self.db.all("SELECT * FROM posts WHERE owner_id=? AND state!='ARCHIVED' ORDER BY updated_at DESC, id DESC LIMIT ?",
                           (owner_id, limit))
        return [self.serialize(r, brief=True) for r in rows]

    def get(self, owner_id: int, post_id: int) -> dict:
        return self.serialize(self.row(owner_id, post_id))

    def counts(self, owner_id: int) -> dict:
        out = {s: 0 for s in BOARD_STATES}
        for r in self.db.all("SELECT state, COUNT(*) c FROM posts WHERE owner_id=? AND state!='ARCHIVED' GROUP BY state", (owner_id,)):
            out[r["state"]] = r["c"]
        return out

    # ---- validation -------------------------------------------------------------------------------
    def checks(self, post, assets=None) -> list:
        assets = self.assets(post["id"]) if assets is None else assets
        out = []
        full = caption_full(post)
        if not (post["caption"] or "").strip():
            out.append({"level": "error", "text": "Add a caption."})
        elif len(full) > MAX_CAPTION:
            out.append({"level": "error", "text": f"Caption and hashtags are {len(full)} characters. The limit is {MAX_CAPTION}."})
        else:
            out.append({"level": "ok", "text": f"Caption {len(full)} of {MAX_CAPTION} characters"})
        mt, n = post["media_type"], len(assets)
        need = {"REEL": "1 video", "IMAGE": "1 image", "STORY": "1 video or image", "CAROUSEL": "2 to 10 images or videos"}[mt]
        ok_count = (2 <= n <= 10) if mt == "CAROUSEL" else n == 1
        if n == 0:
            out.append({"level": "error", "text": f"Add media: this {mt.lower()} needs {need}."})
        elif not ok_count:
            out.append({"level": "error", "text": f"This {mt.lower()} needs {need}, but has {n}."})
        for a in assets:
            label = f"File {a['position'] + 1}" if len(assets) > 1 else "Media"
            if a["status"] == "error":
                msgs = [c["text"] for c in json.loads(a["checks_json"] or "[]") if c["level"] == "error"]
                out.append({"level": "error", "text": f"{label}: {msgs[0] if msgs else 'processing failed'}"})
            elif a["status"] != "ready":
                out.append({"level": "warn", "text": f"{label} is still being prepared."})
            else:
                out.extend({"level": c["level"], "text": f"{label}: {c['text']}"} for c in json.loads(a["checks_json"] or "[]")
                           if c["level"] != "ok" or len(assets) == 1)
        if post["scheduled_for"]:
            if parse_iso(post["scheduled_for"]) < datetime.now(timezone.utc):
                out.append({"level": "warn", "text": "The scheduled time has passed."})
            else:
                out.append({"level": "ok", "text": "Scheduled for later"})
        return out

    @staticmethod
    def blocking(checks: list) -> bool:
        return any(c["level"] == "error" or "still being prepared" in c["text"] for c in checks)

    def media_hash(self, post_id: int) -> str | None:
        assets = self.assets(post_id)
        if not assets or any(a["status"] != "ready" or not a["sha256"] for a in assets):
            return None
        return _sha("|".join(a["sha256"] for a in assets))

    def valid_approval(self, post):
        row = self.db.one("SELECT * FROM approvals WHERE post_id=? AND revoked_at IS NULL ORDER BY id DESC LIMIT 1", (post["id"],))
        if not row:
            return None
        if row["media_sha256"] != self.media_hash(post["id"]) or row["caption_sha256"] != _sha(caption_full(post)):
            return None
        return row

    def serialize(self, post, brief: bool = False) -> dict:
        assets = self.assets(post["id"])
        d = {k: post[k] for k in ("id", "title", "caption", "hashtags", "media_type", "state", "scheduled_for", "error",
                                  "permalink", "remote_media_id", "created_at", "updated_at")}
        d["brief"] = post["brief"] if not brief else post["brief"][:200]
        d["asset_count"] = len(assets)
        first = next((a for a in assets), None)
        d["thumb"] = f"/api/posts/{post['id']}/media/{first['id']}" if first else None
        d["thumb_kind"] = first["kind"] if first else None
        if brief:
            return d
        checks = self.checks(post, assets)
        approval = self.valid_approval(post)
        d.update(
            assets=[{"id": a["id"], "kind": a["kind"], "position": a["position"], "status": a["status"],
                     "width": a["width"], "height": a["height"], "duration": a["duration"], "source": a["source"],
                     "url": f"/api/posts/{post['id']}/media/{a['id']}"} for a in assets],
            checks=checks, approved=bool(approval) and post["state"] in ("APPROVED", "PUBLISHING", "PUBLISHED", "DRY_RUN_COMPLETE"),
            can_approve=post["state"] == "READY_FOR_REVIEW" and not self.blocking(checks),
            busy=bool(self.jobs.active_for_post(post["id"])), dry_run=self.s.dry_run,
            caption_length=len(caption_full(post)), locked=post["state"] in LOCKED)
        return d

    # ---- state ------------------------------------------------------------------------------------
    def touch(self, post) -> None:
        pid = post["id"] if not isinstance(post, int) else post
        r = self.db.one("SELECT id,owner_id,state FROM posts WHERE id=?", (pid,))
        if r:
            self.bus.publish(r["owner_id"], "post", {"id": r["id"], "state": r["state"]})

    def set_state(self, post_id: int, state: str, error: str = "") -> None:
        self.db.execute("UPDATE posts SET state=?, error=?, updated_at=? WHERE id=?", (state, error, now_iso(), post_id))
        self.touch(post_id)

    def refresh_state(self, post_id: int) -> None:
        post = self.db.one("SELECT * FROM posts WHERE id=?", (post_id,))
        if not post or post["state"] not in ("DRAFT", "RENDERING", "READY_FOR_REVIEW"):
            self.touch(post_id)
            return
        busy = [j for j in self.jobs.active_for_post(post_id) if j["kind"] in ("generate_content", "normalize", "render_template")]
        if busy:
            new = "RENDERING"
        else:
            new = "DRAFT" if self.blocking(self.checks(post)) else "READY_FOR_REVIEW"
        if new != post["state"]:
            self.set_state(post_id, new)
            if new == "READY_FOR_REVIEW":
                title = post["title"] or f"Post {post_id}"
                self.activity.log(post["owner_id"], f"{title} is ready for your review.", "attention", post_id)
                self.notifier.attention(f"{title} is ready for your review.")
        else:
            self.touch(post_id)

    def revoke_approval(self, post_id: int) -> None:
        self.db.execute("UPDATE approvals SET revoked_at=? WHERE post_id=? AND revoked_at IS NULL", (now_iso(), post_id))

    # ---- actions ----------------------------------------------------------------------------------
    def create(self, owner_id: int, *, title: str = "", brief: str = "", media_type: str = "REEL",
               auto_render: bool = False, caption: str = "", hashtags: str = "") -> int:
        title = clean_text(title, "Title", 120)
        brief = clean_text(brief, "Brief", 4000)
        caption = clean_text(caption, "Caption", MAX_CAPTION)
        hashtags = clean_hashtags(hashtags)
        if media_type not in MEDIA_TYPES:
            raise ServiceError("Choose a post type: reel, image, carousel or story.")
        if not (title or brief or caption):
            raise ServiceError("Give the post a title or a short brief.")
        ts = now_iso()
        cur = self.db.execute("INSERT INTO posts(owner_id,title,brief,caption,hashtags,media_type,state,created_at,updated_at) "
                              "VALUES(?,?,?,?,?,?,?,?,?)",
                              (owner_id, title or (brief[:60] if brief else "Untitled"), brief, caption, hashtags,
                               media_type, "DRAFT", ts, ts))
        pid = cur.lastrowid
        self.activity.log(owner_id, f"Created post {pid}: {title or brief[:60]}", "info", pid, "Create")
        if brief and not caption:
            self.jobs.enqueue(owner_id, "generate_content", pid, {"auto_render": bool(auto_render)})
        elif auto_render and brief:
            self.jobs.enqueue(owner_id, "render_template", pid, {"text": brief})
        self.refresh_state(pid)
        return pid

    def update(self, owner_id: int, post_id: int, data: dict) -> dict:
        post = self.row(owner_id, post_id)
        if post["state"] in LOCKED:
            raise ServiceError("This post has been published (or is being published), so it can't be edited.", 409)
        sets, vals, changed_content = [], [], False
        if "title" in data:
            sets.append("title=?"); vals.append(clean_text(data["title"], "Title", 120))
        if "brief" in data:
            sets.append("brief=?"); vals.append(clean_text(data["brief"], "Brief", 4000))
        if "caption" in data:
            new = clean_text(data["caption"], "Caption", MAX_CAPTION)
            changed_content |= new != post["caption"]
            sets.append("caption=?"); vals.append(new)
        if "hashtags" in data:
            new = clean_hashtags(data["hashtags"])
            changed_content |= new != post["hashtags"]
            sets.append("hashtags=?"); vals.append(new)
        if "media_type" in data:
            if data["media_type"] not in MEDIA_TYPES:
                raise ServiceError("Choose a post type: reel, image, carousel or story.")
            changed_content |= data["media_type"] != post["media_type"]
            sets.append("media_type=?"); vals.append(data["media_type"])
        if "scheduled_for" in data:
            sf = data["scheduled_for"]
            if sf in (None, ""):
                sets.append("scheduled_for=NULL")
            else:
                try:
                    when = parse_iso(str(sf))
                except ValueError:
                    raise ServiceError("That date and time is not valid.")
                if when < datetime.now(timezone.utc):
                    raise ServiceError("Pick a time in the future.")
                sets.append("scheduled_for=?"); vals.append(when.astimezone(timezone.utc).isoformat(timespec="seconds"))
        if not sets:
            return self.get(owner_id, post_id)
        sets.append("updated_at=?"); vals.append(now_iso())
        self.db.execute(f"UPDATE posts SET {', '.join(sets)} WHERE id=?", (*vals, post_id))
        if changed_content and post["state"] in ("APPROVED", "READY_FOR_REVIEW", "FAILED", "REJECTED", "DRY_RUN_COMPLETE"):
            self.revoke_approval(post_id)
            if post["state"] in ("APPROVED", "FAILED", "REJECTED", "DRY_RUN_COMPLETE"):
                self.set_state(post_id, "DRAFT")
            self.activity.log(owner_id, f"Post {post_id} was edited, so it needs approval again.", "info", post_id, "Modify")
        elif post["state"] in ("FAILED", "REJECTED"):
            self.set_state(post_id, "DRAFT")
        self.refresh_state(post_id)
        return self.get(owner_id, post_id)

    def approve(self, owner_id: int, post_id: int) -> dict:
        post = self.row(owner_id, post_id)
        if post["state"] != "READY_FOR_REVIEW":
            raise ServiceError("Only a post that is ready for review can be approved.", 409)
        checks = self.checks(post)
        if self.blocking(checks):
            raise ServiceError("Fix the problems listed under Checks first.", 409)
        mh = self.media_hash(post_id)
        if not mh:
            raise ServiceError("The media is not ready yet.", 409)
        self.revoke_approval(post_id)
        self.db.execute("INSERT INTO approvals(owner_id,post_id,media_sha256,caption_sha256,approved_at) VALUES(?,?,?,?,?)",
                        (owner_id, post_id, mh, _sha(caption_full(post)), now_iso()))
        self.set_state(post_id, "APPROVED")
        self.activity.log(owner_id, f"You approved post {post_id}.", "success", post_id, "Modify")
        return self.get(owner_id, post_id)

    def send_back(self, owner_id: int, post_id: int) -> dict:
        post = self.row(owner_id, post_id)
        if post["state"] in LOCKED:
            raise ServiceError("This post is already published.", 409)
        self.revoke_approval(post_id)
        self.set_state(post_id, "DRAFT")
        self.refresh_state(post_id)
        self.activity.log(owner_id, f"Post {post_id} sent back for edits.", "info", post_id, "Modify")
        return self.get(owner_id, post_id)

    def reject(self, owner_id: int, post_id: int) -> dict:
        post = self.row(owner_id, post_id)
        if post["state"] in LOCKED:
            raise ServiceError("This post is already published.", 409)
        self.revoke_approval(post_id)
        self.set_state(post_id, "REJECTED")
        self.activity.log(owner_id, f"You rejected post {post_id}.", "info", post_id, "Modify")
        return self.get(owner_id, post_id)

    def archive(self, owner_id: int, post_id: int) -> None:
        post = self.row(owner_id, post_id)
        if post["state"] == "PUBLISHING":
            raise ServiceError("Wait until publishing finishes.", 409)
        self.revoke_approval(post_id)
        self.set_state(post_id, "ARCHIVED")
        self.activity.log(owner_id, f"Removed post {post_id} from the board.", "info", post_id, "Modify")

    def request_publish(self, owner_id: int, post_id: int) -> dict:
        """Queue publishing of an approved post now, or leave it for the scheduler if a future time is set."""
        post = self.row(owner_id, post_id)
        if post["state"] not in ("APPROVED", "FAILED", "DRY_RUN_COMPLETE"):
            raise ServiceError("Approve the post before publishing it.", 409)
        if not self.valid_approval(post):
            self.set_state(post_id, "DRAFT")
            self.refresh_state(post_id)
            raise ServiceError("The post changed after it was approved. Review it and approve it again.", 409)
        if not self.s.dry_run and not self.s.ig_configured:
            raise ServiceError("Instagram is not connected yet. Add IG_USER_ID and IG_ACCESS_TOKEN to .env, or keep DRY_RUN=1 to test.", 409)
        if post["scheduled_for"] and parse_iso(post["scheduled_for"]) > datetime.now(timezone.utc):
            if post["state"] in ("FAILED", "DRY_RUN_COMPLETE"):
                self.set_state(post_id, "APPROVED")
            self.activity.log(owner_id, f"Post {post_id} is scheduled and will publish at its set time.", "info", post_id, "External Action")
            return self.get(owner_id, post_id)
        self.set_state(post_id, "PUBLISHING")
        self.jobs.enqueue(owner_id, "publish", post_id)
        mode = "Dry run: " if self.s.dry_run else ""
        self.activity.log(owner_id, f"{mode}publishing post {post_id} started.", "info", post_id, "External Action")
        return self.get(owner_id, post_id)
