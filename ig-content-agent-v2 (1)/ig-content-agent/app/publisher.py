"""Publishing. Every path re-checks the approval itself, so a buggy route can't publish an unapproved post."""
from __future__ import annotations

import json
import re
import urllib.request

from .db import now_iso
from .instagram import GraphClient, InstagramError
from .media import safe_child, sha256_file
from .pipeline import PublishRefused
from .services import caption_full


class Publisher:
    def __init__(self, ctx, graph: GraphClient | None = None):
        self.ctx = ctx
        self.graph = graph or GraphClient(ctx.settings)

    def _verify(self, owner_id: int, post_id: int):
        c = self.ctx
        post = c.posts.row(owner_id, post_id)
        if post["state"] not in ("PUBLISHING", "APPROVED"):
            raise PublishRefused("This post is not in a state that can be published.")
        approval = c.posts.valid_approval(post)
        if not approval:
            c.posts.set_state(post_id, "DRAFT")
            c.posts.refresh_state(post_id)
            raise PublishRefused("The post changed after it was approved (or was never approved). Review it and approve it again.")
        assets = c.posts.assets(post_id)
        if not assets or any(a["status"] != "ready" for a in assets):
            raise PublishRefused("The media is not ready.")
        for a in assets:  # the file on disk must be exactly what was approved
            path = safe_child(c.settings.media_dir, a["ready_key"])
            if not path.exists() or sha256_file(path) != a["sha256"]:
                raise PublishRefused("A media file is missing or was changed after approval. Approve the post again.")
        return post, assets

    def run(self, owner_id: int, post_id: int) -> None:
        c = self.ctx
        post, assets = self._verify(owner_id, post_id)
        if post["state"] == "APPROVED":
            c.posts.set_state(post_id, "PUBLISHING")
        if c.settings.dry_run:
            return self._dry_run(owner_id, post, assets)
        if not c.settings.ig_configured:
            raise PublishRefused("Instagram is not connected. Add IG_USER_ID and IG_ACCESS_TOKEN to .env.")
        if not c.settings.public_media_base_url:
            raise PublishRefused("PUBLIC_MEDIA_BASE_URL is not set. Instagram needs a public link to fetch the media (see docs/REMOTE_ACCESS.md).")
        try:
            lim = self.graph.publishing_limit()
            if lim.get("remaining") == 0:
                raise PublishRefused("Instagram's publishing limit for the last 24 hours has been reached. Try again later.")
        except InstagramError:
            pass  # the limit check is advisory; a real limit error will surface on publish
        attempt = c.db.execute("INSERT INTO publish_attempts(owner_id,post_id,mode,status,created_at) VALUES(?,?,?,?,?)",
                               (owner_id, post_id, "live", "running", now_iso())).lastrowid
        try:
            media_id = self._publish_live(post, assets, attempt)
        finally:
            for a in assets:
                c.public_links.revoke_asset(a["id"])
        permalink = self.graph.permalink(media_id)
        c.db.execute("UPDATE publish_attempts SET status='ok', remote_media_id=? WHERE id=?", (media_id, attempt))
        c.db.execute("UPDATE posts SET remote_media_id=?, permalink=?, state='PUBLISHED', error='', updated_at=? WHERE id=?",
                     (media_id, permalink, now_iso(), post_id))
        c.posts.touch(post_id)
        c.activity.log(owner_id, f"Post {post_id} is live on Instagram." + (f" {permalink}" if permalink else ""), "success", post_id,
                       "External Action")
        c.notifier.attention(f"Post {post_id} is now live on Instagram.")

    def _publish_live(self, post, assets, attempt_id: int) -> str:
        c, g = self.ctx, self.graph
        caption = caption_full(post)
        mt = post["media_type"]

        def url_for(a):
            return c.public_links.create(a["id"], a["ready_key"])

        if mt == "CAROUSEL":
            children = []
            for a in assets:
                cid = g.create_container(media_type="CAROUSEL_ITEM", media_url=url_for(a), carousel_item=True,
                                         is_video=a["kind"] == "video")
                g.wait_until_ready(cid)
                children.append(cid)
            container = g.create_container(media_type="CAROUSEL", caption=caption, children=children)
        else:
            a = assets[0]
            container = g.create_container(media_type=mt, media_url=url_for(a), caption=caption, is_video=a["kind"] == "video")
        c.db.execute("UPDATE publish_attempts SET container_id=? WHERE id=?", (container, attempt_id))
        g.wait_until_ready(container)
        return g.publish(container)

    def _dry_run(self, owner_id: int, post, assets) -> None:
        """Everything except the final call to Instagram."""
        c = self.ctx
        notes = ["approval and file hashes verified"]
        base = c.settings.public_media_base_url
        if base:
            try:
                for a in assets:
                    url = c.public_links.create(a["id"], a["ready_key"])
                    req = urllib.request.Request(c.public_links.local_url(url), method="HEAD")
                    with urllib.request.urlopen(req, timeout=10) as r:
                        if r.status != 200:
                            raise OSError(r.status)
                notes.append("media link served locally")
            except Exception:
                notes.append("media link could NOT be served locally (is the app running with the public media server?)")
            finally:
                for a in assets:
                    c.public_links.revoke_asset(a["id"])
        else:
            notes.append("PUBLIC_MEDIA_BASE_URL not set yet (needed for live posting)")
        if not c.settings.ig_configured:
            notes.append("Instagram not connected yet")
        c.db.execute("INSERT INTO publish_attempts(owner_id,post_id,mode,status,error,created_at) VALUES(?,?,?,?,?,?)",
                     (owner_id, post["id"], "dry_run", "ok", "; ".join(notes)[:300], now_iso()))
        c.posts.set_state(post["id"], "DRY_RUN_COMPLETE")
        c.activity.log(owner_id, f"Dry run finished for post {post['id']}. Nothing was posted. ({'; '.join(notes)})", "success",
                       post["id"], "External Action")
        c.notifier.attention(f"Dry run finished for post {post['id']}. Nothing was posted.")
