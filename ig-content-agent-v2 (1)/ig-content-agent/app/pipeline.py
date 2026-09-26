"""File handling for posts, the background job runner, the inbox watcher and the scheduler."""
from __future__ import annotations

import json
import re
import shutil
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .db import now_iso
from .instagram import InstagramError
from .llm import LLMError, fallback_content, generate_content
from .media import (ALLOWED_EXT, IMAGE_EXT, VIDEO_EXT, Ffmpeg, MediaError, normalize_image, normalize_video,
                    random_key, render_text_video, safe_child, script_to_lines, sha256_file, sniff_kind, spec_checks)
from .services import LOCKED, PostService, ServiceError


class MediaService:
    def __init__(self, settings, db, posts: PostService, jobs, activity, ff: Ffmpeg):
        self.s, self.db, self.posts, self.jobs, self.activity, self.ff = settings, db, posts, jobs, activity, ff

    def path_of(self, asset, ready: bool = True) -> Path:
        key = asset["ready_key"] if (ready and asset["ready_key"]) else asset["storage_key"]
        return safe_child(self.s.media_dir, key)

    def save_upload(self, owner_id: int, post_id: int, file_storage, source: str = "upload") -> int:
        name = file_storage.filename or ""
        tmp = self.s.media_dir / "tmp" / random_key(".part")
        limit = self.s.max_upload_mb * 1024 * 1024
        size = 0
        try:
            with open(tmp, "wb") as out:
                while True:
                    chunk = file_storage.stream.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > limit:
                        raise MediaError(f"That file is larger than the {self.s.max_upload_mb} MB limit.")
                    out.write(chunk)
            if size == 0:
                raise MediaError("That file is empty.")
            return self._ingest(owner_id, post_id, tmp, name, source)
        finally:
            tmp.unlink(missing_ok=True)

    def _ingest(self, owner_id: int, post_id: int, tmp: Path, original_name: str, source: str) -> int:
        post = self.posts.row(owner_id, post_id)
        if post["state"] in LOCKED:
            raise MediaError("This post is already published, so its media can't change.")
        ext = Path(original_name).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise MediaError("Unsupported file type. Use MP4, MOV, M4V, WEBM, GIF, JPG or PNG.")
        with open(tmp, "rb") as f:
            head = f.read(32)
        kind = sniff_kind(head)
        if not kind:
            raise MediaError("This file is not a real video or image, even though its name says it is.")
        if (kind == "image") != (ext in IMAGE_EXT):
            raise MediaError("The file's content does not match its extension.")
        mt = post["media_type"]
        if mt == "REEL" and kind != "video":
            raise MediaError("A Reel needs a video. Change the post type to Image or Story to use a picture.")
        if mt == "IMAGE" and kind != "image":
            raise MediaError("An Image post needs a picture. Change the post type to Reel to use a video.")
        final_ext = ext
        if kind == "image":
            final_ext = ".png" if head[:4] == b"\x89PNG" else ".jpg"
        key = random_key(final_ext)
        dest = safe_child(self.s.media_dir, key)
        shutil.copyfile(tmp, dest)
        try:
            info = self.ff.probe(dest)
        except MediaError:
            dest.unlink(missing_ok=True)
            raise
        if mt != "CAROUSEL":
            self._drop_assets(post_id)
        if post["state"] in ("APPROVED", "READY_FOR_REVIEW", "FAILED", "REJECTED", "DRY_RUN_COMPLETE"):
            self.posts.revoke_approval(post_id)
            self.posts.set_state(post_id, "DRAFT")
        pos = self.db.one("SELECT COUNT(*) c FROM assets WHERE post_id=?", (post_id,))["c"]
        if mt == "CAROUSEL" and pos >= 10:
            dest.unlink(missing_ok=True)
            raise MediaError("A carousel can have at most 10 files.")
        checks = spec_checks(kind, info, mt)
        cur = self.db.execute(
            "INSERT INTO assets(owner_id,post_id,position,kind,source,original_name,storage_key,status,size_bytes,width,height,"
            "duration,checks_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (owner_id, post_id, pos, kind, source, re.sub(r"[^\w.\- ]", "_", Path(original_name).name)[:120], key, "raw",
             dest.stat().st_size, info["width"], info["height"], info["duration"], json.dumps(checks), now_iso()))
        self.jobs.enqueue(owner_id, "normalize", post_id, {"asset_id": cur.lastrowid})
        self.activity.log(owner_id, f"Added a {kind} to post {post_id}. Preparing it for Instagram.", "info", post_id, "Create")
        self.posts.refresh_state(post_id)
        return cur.lastrowid

    def _drop_assets(self, post_id: int) -> None:
        for a in self.posts.assets(post_id):
            for k in {a["storage_key"], a["ready_key"]}:
                if k:
                    try:
                        safe_child(self.s.media_dir, k).unlink(missing_ok=True)
                    except MediaError:
                        pass
            self.db.execute("DELETE FROM public_links WHERE asset_id=?", (a["id"],))
            self.db.execute("DELETE FROM assets WHERE id=?", (a["id"],))

    def normalize_asset(self, asset_id: int) -> None:
        a = self.db.one("SELECT * FROM assets WHERE id=?", (asset_id,))
        if not a:
            return
        post = self.db.one("SELECT * FROM posts WHERE id=?", (a["post_id"],))
        src = self.path_of(a, ready=False)
        ext = ".jpg" if a["kind"] == "image" else ".mp4"
        key = random_key(ext)
        dst = safe_child(self.s.media_dir, key)
        try:
            info = self.ff.probe(src)
            if a["kind"] == "image":
                normalize_image(self.ff, src, dst, info, post["media_type"])
            else:
                normalize_video(self.ff, src, dst)
            out = self.ff.probe(dst)
        except MediaError as e:
            dst.unlink(missing_ok=True)
            self.db.execute("UPDATE assets SET status='error', checks_json=? WHERE id=?",
                            (json.dumps([{"level": "error", "text": str(e)}]), asset_id))
            self.activity.log(a["owner_id"], f"Could not prepare the media for post {a['post_id']}: {e}", "error", a["post_id"], "Create")
            self.posts.refresh_state(a["post_id"])
            raise
        self.db.execute("UPDATE assets SET ready_key=?, status='ready', sha256=?, width=?, height=?, duration=?, size_bytes=?, "
                        "checks_json=? WHERE id=?",
                        (key, sha256_file(dst), out["width"], out["height"], out["duration"], dst.stat().st_size,
                         json.dumps(spec_checks(a["kind"], out, post["media_type"])), asset_id))
        self.activity.log(a["owner_id"], f"Media for post {a['post_id']} is ready ({out['width']}x{out['height']}).", "success",
                          a["post_id"], "Create")
        self.posts.refresh_state(a["post_id"])

    def render_text(self, owner_id: int, post_id: int, lines: list) -> int:
        post = self.posts.row(owner_id, post_id)
        if post["state"] in LOCKED:
            raise MediaError("This post is already published.")
        if post["media_type"] == "IMAGE":
            raise MediaError("Text videos need a Reel, Story or Carousel post.")
        key = random_key(".mp4")
        dst = safe_child(self.s.media_dir, key)
        try:
            render_text_video(self.ff, lines, dst, bg=self.s.brand_bg, fg=self.s.brand_fg, accent=self.s.brand_accent,
                              brand=self.s.brand_name)
            info = self.ff.probe(dst)
        except MediaError:
            dst.unlink(missing_ok=True)
            raise
        if post["media_type"] != "CAROUSEL":
            self._drop_assets(post_id)
        if post["state"] in ("APPROVED", "READY_FOR_REVIEW", "FAILED", "REJECTED", "DRY_RUN_COMPLETE"):
            self.posts.revoke_approval(post_id)
            self.posts.set_state(post_id, "DRAFT")
        pos = self.db.one("SELECT COUNT(*) c FROM assets WHERE post_id=?", (post_id,))["c"]
        cur = self.db.execute(
            "INSERT INTO assets(owner_id,post_id,position,kind,source,original_name,storage_key,ready_key,status,sha256,size_bytes,"
            "width,height,duration,checks_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (owner_id, post_id, pos, "video", "rendered", "text-video.mp4", key, key, "ready", sha256_file(dst),
             dst.stat().st_size, info["width"], info["height"], info["duration"],
             json.dumps(spec_checks("video", info, post["media_type"])), now_iso()))
        self.activity.log(owner_id, f"Built a text video for post {post_id} ({info['duration']:.0f} s).", "success", post_id, "Create")
        self.posts.refresh_state(post_id)
        return cur.lastrowid


class PublishRefused(Exception):
    """The publisher refused on purpose (not approved, changed, limit reached). The message is shown to the owner."""


class JobRunner:
    def __init__(self, ctx):
        self.ctx = ctx

    def run_one(self, kinds: tuple) -> bool:
        c = self.ctx
        job = c.jobs.claim(kinds)
        if not job:
            return False
        try:
            payload = json.loads(job["payload_json"] or "{}")
            getattr(self, f"h_{job['kind']}")(job, payload)
            c.jobs.finish(job["id"])
            if job["post_id"]:
                c.posts.refresh_state(job["post_id"])  # the finished job no longer counts as work in progress
        except InstagramError as e:
            self._instagram_failure(job, e)
        except PublishRefused as e:
            c.jobs.fail(job["id"], str(e))
            self._publish_failed(job, str(e))
        except (MediaError, ServiceError, LLMError) as e:
            msg = getattr(e, "message", None) or str(e)
            c.jobs.fail(job["id"], msg)
            if job["post_id"]:
                c.activity.log(job["owner_id"], f"{job['kind'].replace('_', ' ')} failed for post {job['post_id']}: {msg}", "error",
                               job["post_id"], "Create")
                c.posts.refresh_state(job["post_id"])
        except Exception:
            c.log.exception("Job %s crashed", job["id"])
            c.jobs.fail(job["id"], "Unexpected error. See the server log.")
            if job["post_id"]:
                c.activity.log(job["owner_id"], f"{job['kind'].replace('_', ' ')} hit an unexpected error for post {job['post_id']}.",
                               "error", job["post_id"])
                if job["kind"] == "publish":
                    self._publish_failed(job, "Unexpected error while publishing. See the server log.")
                else:
                    c.posts.refresh_state(job["post_id"])
        return True

    def _instagram_failure(self, job, e: InstagramError) -> None:
        c = self.ctx
        if e.retryable and job["attempts"] < 3:
            delay = 30 * (2 ** (job["attempts"] - 1))
            when = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat(timespec="seconds")
            c.jobs.retry_later(job["id"], when, str(e))
            c.activity.log(job["owner_id"], f"Publishing post {job['post_id']} hit a temporary problem. Trying again in {delay} s.",
                           "warn", job["post_id"], "External Action")
            return
        c.jobs.fail(job["id"], str(e))
        self._publish_failed(job, str(e))

    def _publish_failed(self, job, msg: str) -> None:
        c = self.ctx
        c.db.execute("INSERT INTO publish_attempts(owner_id,post_id,mode,status,error,created_at) VALUES(?,?,?,?,?,?)",
                     (job["owner_id"], job["post_id"], "dry_run" if c.settings.dry_run else "live", "failed", msg[:300], now_iso()))
        row = c.db.one("SELECT state FROM posts WHERE id=?", (job["post_id"],))
        if row and row["state"] in ("PUBLISHING", "APPROVED"):
            c.posts.set_state(job["post_id"], "FAILED", msg[:300])
        c.activity.log(job["owner_id"], f"Publishing post {job['post_id']} failed: {msg}", "attention", job["post_id"], "External Action")
        c.notifier.attention(f"Publishing post {job['post_id']} failed. {msg}")

    # ---- handlers ---------------------------------------------------------------------------------
    def h_generate_content(self, job, p):
        c = self.ctx
        post = c.posts.row(job["owner_id"], job["post_id"])
        try:
            data = generate_content(c.llm, post["brief"], post["title"])
        except LLMError as e:
            c.activity.log(job["owner_id"], f"The AI writer was unavailable ({e}). Used the simple offline writer instead.", "warn",
                           post["id"], "Create")
            data = fallback_content(post["brief"] or post["title"])
        force = bool(p.get("force"))
        sets, vals = [], []
        if force or not post["caption"].strip():
            sets.append("caption=?"); vals.append(data["caption"])
        if force or not post["hashtags"].strip():
            sets.append("hashtags=?"); vals.append(data["hashtags"])
        if sets:
            sets.append("updated_at=?"); vals.append(now_iso())
            c.db.execute(f"UPDATE posts SET {', '.join(sets)} WHERE id=?", (*vals, post["id"]))
            if force:
                c.posts.revoke_approval(post["id"])
                if post["state"] in ("APPROVED", "FAILED", "REJECTED", "DRY_RUN_COMPLETE"):
                    c.posts.set_state(post["id"], "DRAFT")
        c.activity.log(job["owner_id"], f"Wrote the caption for post {post['id']} ({data['source']}).", "success", post["id"], "Create")
        fresh = c.posts.row(job["owner_id"], post["id"])
        if p.get("auto_render") and fresh["media_type"] in ("REEL", "STORY") and not c.posts.assets(post["id"]):
            c.jobs.enqueue(job["owner_id"], "render_template", post["id"], {"lines": data["lines"]})
        c.posts.refresh_state(post["id"])

    def h_render_template(self, job, p):
        c = self.ctx
        lines = p.get("lines") or script_to_lines(p.get("text", ""))
        c.media.render_text(job["owner_id"], job["post_id"], lines)

    def h_normalize(self, job, p):
        self.ctx.media.normalize_asset(int(p["asset_id"]))

    def h_publish(self, job, p):
        self.ctx.publisher.run(job["owner_id"], job["post_id"])


class Runtime:
    """Owns the background threads: two job workers, the inbox watcher and the scheduler."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.stop_event = threading.Event()
        self.threads: list = []

    def start(self) -> None:
        c = self.ctx
        c.jobs.recover_stuck()
        for name, target in (("media-worker", self._media_loop), ("publish-worker", self._publish_loop),
                             ("watcher", self._watch_loop)):
            t = threading.Thread(target=target, name=name, daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self) -> None:
        self.stop_event.set()
        for t in self.threads:
            t.join(timeout=5)

    def _beat(self, name: str) -> None:
        self.ctx.db.kv_set(f"heartbeat:{name}", now_iso())

    def _media_loop(self):
        while not self.stop_event.is_set():
            self._beat("media")
            try:
                did = self.ctx.runner.run_one(("generate_content", "normalize", "render_template"))
            except Exception:
                self.ctx.log.exception("media worker error")
                did = False
            if not did:
                self.stop_event.wait(1.0)

    def _publish_loop(self):
        while not self.stop_event.is_set():
            self._beat("publish")
            try:
                did = self.ctx.runner.run_one(("publish",))
            except Exception:
                self.ctx.log.exception("publish worker error")
                did = False
            if not did:
                self.stop_event.wait(1.5)

    def _watch_loop(self):
        watcher = InboxWatcher(self.ctx)
        last_purge = 0.0
        while not self.stop_event.is_set():
            self._beat("watcher")
            try:
                watcher.scan_once()
                scan_schedule(self.ctx)
                if time.monotonic() - last_purge > 300:
                    self.ctx.public_links.purge_expired()
                    last_purge = time.monotonic()
            except Exception:
                self.ctx.log.exception("watcher error")
            self.stop_event.wait(3.0)


def owner_id_of(ctx) -> int | None:
    row = ctx.db.one("SELECT id FROM users ORDER BY id LIMIT 1")
    return row["id"] if row else None


def scan_schedule(ctx) -> int:
    """Publish approved posts whose scheduled time has arrived. They still carry the owner's approval."""
    n = 0
    rows = ctx.db.all("SELECT id, owner_id FROM posts WHERE state='APPROVED' AND scheduled_for IS NOT NULL AND scheduled_for<=?",
                      (now_iso(),))
    for r in rows:
        try:
            ctx.posts.request_publish(r["owner_id"], r["id"])
            n += 1
        except ServiceError as e:
            ctx.activity.log(r["owner_id"], f"Scheduled post {r['id']} could not start: {e.message}", "attention", r["id"])
            ctx.db.execute("UPDATE posts SET scheduled_for=NULL WHERE id=?", (r["id"],))
    return n


class InboxWatcher:
    """Drop a file (for example a Swishy export) into the inbox folder and it becomes a draft post."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.seen: dict = {}

    def scan_once(self) -> int:
        c = self.ctx
        owner = owner_id_of(c)
        if not owner:
            return 0
        imported = 0
        for p in sorted(c.settings.inbox_dir.iterdir()):
            if not p.is_file() or p.name.startswith(".") or p.suffix.lower() not in ALLOWED_EXT:
                continue
            st = p.stat()
            sig = (st.st_size, st.st_mtime_ns)
            prev = self.seen.get(p)
            stable = (prev[1] + 1) if prev and prev[0] == sig else 0
            self.seen[p] = (sig, stable)
            if stable >= 1 and st.st_size > 0:
                self._import(owner, p)
                self.seen.pop(p, None)
                imported += 1
        return imported

    def _import(self, owner: int, path: Path) -> None:
        c = self.ctx
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe = re.sub(r"[^\w.\-]", "_", path.name)
        kind = sniff_kind(path.open("rb").read(32))
        mt = "IMAGE" if path.suffix.lower() in IMAGE_EXT else "REEL"
        title = re.sub(r"[_\-]+", " ", path.stem)[:80] or "New file"
        pid = None
        try:
            pid = c.posts.create(owner, title=title, media_type=mt)
            tmp = c.settings.media_dir / "tmp" / random_key(".part")
            shutil.copyfile(path, tmp)
            try:
                c.media._ingest(owner, pid, tmp, path.name, "swishy_inbox")
            finally:
                tmp.unlink(missing_ok=True)
            shutil.move(str(path), str(c.settings.inbox_dir / "processed" / f"{stamp}-{safe}"))
            c.activity.log(owner, f"Picked up {path.name} from the inbox as post {pid}. It needs a caption.", "attention", pid, "Create")
            c.notifier.attention(f"New file from the inbox: {title}. It needs a caption.")
        except (MediaError, ServiceError) as e:
            if pid:
                c.db.execute("UPDATE posts SET state='ARCHIVED' WHERE id=?", (pid,))
            shutil.move(str(path), str(c.settings.inbox_dir / "rejected" / f"{stamp}-{safe}"))
            c.activity.log(owner, f"Inbox file {path.name} was rejected: {getattr(e, 'message', None) or e}", "error", None, "Create")
