import io
import json

from werkzeug.datastructures import FileStorage

from app.instagram import GraphClient
from app.publisher import Publisher
from tests.helpers import AppCase, make_image

TOKEN = "EAAB" + "x" * 60


class FakeGraph:
    """Stands in for Instagram. Records every call; nothing touches the network."""

    def __init__(self, fail_create=None, limit=None, poll=("IN_PROGRESS", "FINISHED")):
        self.calls, self.fail_create, self.limit, self.poll = [], fail_create, limit, list(poll)
        self.n = 0

    def __call__(self, method, url, params):
        self.calls.append((method, url, dict(params)))
        if url.endswith("/content_publishing_limit"):
            return 200, {"data": [{"quota_usage": self.limit if self.limit is not None else 1, "config": {"quota_total": 50}}]}
        if url.endswith("/media") and method == "POST":
            if self.fail_create:
                return self.fail_create
            self.n += 1
            return 200, {"id": f"C{self.n}"}
        if url.endswith("/media_publish"):
            return 200, {"id": "M1"}
        if "fields" in params and params["fields"].startswith("status_code"):
            return 200, {"status_code": self.poll.pop(0) if len(self.poll) > 1 else self.poll[0]}
        if params.get("fields") == "permalink":
            return 200, {"permalink": "https://www.instagram.com/p/abc/"}
        return 404, {"error": {"message": "unexpected " + url, "code": 1}}


class LivePublishTests(AppCase):
    settings_overrides = dict(dry_run=False, ig_user_id="1789", ig_access_token=TOKEN, public_media_base_url="https://media.example.com")

    def use(self, fake):
        self.ctx.publisher = Publisher(self.ctx, GraphClient(self.settings, transport=fake, sleep=lambda s: None))
        return fake

    def approved(self, **kw):
        pid = self.ready_post(**kw)
        self.ctx.posts.approve(self.owner, pid)
        return pid

    def test_reel_published_with_exact_parameters(self):
        fake = self.use(FakeGraph())
        pid = self.approved()
        self.ctx.posts.request_publish(self.owner, pid)
        self.run_jobs(("publish",))
        p = self.ctx.posts.get(self.owner, pid)
        self.assertEqual(p["state"], "PUBLISHED")
        self.assertEqual(p["permalink"], "https://www.instagram.com/p/abc/")
        create = next(c for c in fake.calls if c[0] == "POST" and c[1].endswith("/1789/media"))
        self.assertEqual(create[2]["media_type"], "REELS")
        self.assertTrue(create[2]["video_url"].startswith("https://media.example.com/m/"))
        self.assertIn(p["caption"][:20], create[2]["caption"])
        self.assertEqual(create[2]["access_token"], TOKEN)  # sent in the body, not in the URL
        self.assertNotIn(TOKEN, create[1])
        self.assertEqual(self.ctx.db.one("SELECT COUNT(*) c FROM public_links")["c"], 0)  # link revoked afterwards

    def test_token_never_appears_in_activity_or_attempt_records(self):
        self.use(FakeGraph(fail_create=(400, {"error": {"code": 190, "message": f"bad token {TOKEN}"}})))
        pid = self.approved()
        self.ctx.posts.request_publish(self.owner, pid)
        self.run_jobs(("publish",))
        p = self.ctx.posts.get(self.owner, pid)
        self.assertEqual(p["state"], "FAILED")
        self.assertIn("access token", p["error"])
        dump = json.dumps([dict(r) for r in self.ctx.db.all("SELECT * FROM activity")] + [dict(r) for r in self.ctx.db.all("SELECT * FROM publish_attempts")] + [p])
        self.assertNotIn(TOKEN, dump)

    def test_temporary_error_is_retried_not_failed(self):
        self.use(FakeGraph(fail_create=(503, {"error": {"code": 2, "message": "temporary"}})))
        pid = self.approved()
        self.ctx.posts.request_publish(self.owner, pid)
        self.run_jobs(("publish",), limit=1)
        job = self.ctx.db.one("SELECT status, attempts FROM jobs WHERE kind='publish'")
        self.assertEqual((job["status"], job["attempts"]), ("queued", 1))
        self.assertEqual(self.ctx.posts.get(self.owner, pid)["state"], "PUBLISHING")

    def test_daily_limit_blocks_publishing(self):
        fake = self.use(FakeGraph(limit=50))
        pid = self.approved()
        self.ctx.posts.request_publish(self.owner, pid)
        self.run_jobs(("publish",))
        p = self.ctx.posts.get(self.owner, pid)
        self.assertEqual(p["state"], "FAILED")
        self.assertIn("limit", p["error"].lower())
        self.assertFalse(any(c[1].endswith("/media") for c in fake.calls))

    def test_processing_error_from_instagram(self):
        self.use(FakeGraph(poll=("ERROR",)))
        pid = self.approved()
        self.ctx.posts.request_publish(self.owner, pid)
        self.run_jobs(("publish",))
        self.assertEqual(self.ctx.posts.get(self.owner, pid)["state"], "FAILED")

    def test_carousel_creates_children_then_parent(self):
        fake = self.use(FakeGraph(poll=("FINISHED",)))
        pid = self.ctx.posts.create(self.owner, title="c", brief="", caption="Carousel caption", hashtags="#a", media_type="CAROUSEL")
        img = make_image(self.tmp + "/a.png")
        for _ in range(2):
            self.ctx.media.save_upload(self.owner, pid, FileStorage(stream=io.BytesIO(img.read_bytes()), filename="a.png"))
        self.run_jobs()
        self.ctx.posts.approve(self.owner, pid)
        self.ctx.posts.request_publish(self.owner, pid)
        self.run_jobs(("publish",))
        self.assertEqual(self.ctx.posts.get(self.owner, pid)["state"], "PUBLISHED")
        creates = [c[2] for c in fake.calls if c[0] == "POST" and c[1].endswith("/media")]
        self.assertEqual([c.get("is_carousel_item") for c in creates], ["true", "true", None])
        self.assertEqual(creates[2]["media_type"], "CAROUSEL")
        self.assertEqual(creates[2]["children"], "C1,C2")
        self.assertIn("Carousel caption", creates[2]["caption"])

    def test_missing_setup_is_explained_not_crashed(self):
        from dataclasses import replace
        self.ctx.settings = replace(self.settings, public_media_base_url="")
        self.ctx.publisher = Publisher(self.ctx, GraphClient(self.ctx.settings, transport=FakeGraph()))
        pid = self.approved()
        self.ctx.posts.request_publish(self.owner, pid)
        self.run_jobs(("publish",))
        p = self.ctx.posts.get(self.owner, pid)
        self.assertEqual(p["state"], "FAILED")
        self.assertIn("PUBLIC_MEDIA_BASE_URL", p["error"])


class NotConnectedTests(AppCase):
    settings_overrides = dict(dry_run=False)

    def test_live_mode_without_instagram_refuses_early(self):
        from app.services import ServiceError
        pid = self.ready_post()
        self.ctx.posts.approve(self.owner, pid)
        with self.assertRaises(ServiceError) as cm:
            self.ctx.posts.request_publish(self.owner, pid)
        self.assertIn("not connected", cm.exception.message)


if __name__ == "__main__":
    import unittest
    unittest.main()
