import json
import shutil
import threading
import time
import unittest
import urllib.request
import http.client
import re
from datetime import datetime, timedelta, timezone

from werkzeug.serving import make_server

from app.pipeline import InboxWatcher, Runtime, scan_schedule
from app.publicmedia import PublicLinks, create_public_app
from tests.helpers import AppCase, PASSWORD, make_video


class InboxAndScheduleTests(AppCase):
    def test_swishy_export_dropped_in_inbox_becomes_a_draft(self):
        w = InboxWatcher(self.ctx)
        make_video(self.settings.inbox_dir / "My_Swishy_Export.mp4", seconds=2, size="1280x720")
        self.assertEqual(w.scan_once(), 0)  # first sight: wait to be sure the file is finished copying
        self.assertEqual(w.scan_once(), 1)
        posts = self.ctx.posts.list(self.owner)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["title"], "My Swishy Export")
        self.run_jobs()
        p = self.ctx.posts.get(self.owner, posts[0]["id"])
        self.assertEqual(p["assets"][0]["status"], "ready")
        self.assertEqual(p["state"], "DRAFT")  # media is ready, but it still needs a caption
        self.assertIn("Add a caption.", [c["text"] for c in p["checks"]])
        self.assertEqual(len(list((self.settings.inbox_dir / "processed").iterdir())), 1)
        self.assertEqual(list(self.settings.inbox_dir.glob("*.mp4")), [])
        self.assertTrue(any("needs a caption" in a["message"] for a in self.ctx.activity.recent(self.owner)))

    def test_fake_file_in_inbox_is_rejected_and_reported(self):
        w = InboxWatcher(self.ctx)
        (self.settings.inbox_dir / "evil.mp4").write_bytes(b"MZ not a video")
        w.scan_once(); w.scan_once()
        self.assertEqual(self.ctx.posts.list(self.owner), [])
        self.assertEqual(len(list((self.settings.inbox_dir / "rejected").iterdir())), 1)
        self.assertTrue(any(a["level"] == "error" for a in self.ctx.activity.recent(self.owner)))

    def test_scheduler_publishes_only_approved_posts_when_due(self):
        due = self.ready_post()
        not_approved = self.ready_post(title="Other")
        self.ctx.posts.approve(self.owner, due)
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds")
        future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(timespec="seconds")
        self.ctx.db.execute("UPDATE posts SET scheduled_for=? WHERE id=?", (past, due))
        self.ctx.db.execute("UPDATE posts SET scheduled_for=? WHERE id=?", (past, not_approved))
        self.assertEqual(scan_schedule(self.ctx), 1)
        self.assertEqual(self.ctx.posts.get(self.owner, due)["state"], "PUBLISHING")
        self.assertEqual(self.ctx.posts.get(self.owner, not_approved)["state"], "READY_FOR_REVIEW")

    def test_jobs_survive_a_restart(self):
        self.ctx.jobs.enqueue(self.owner, "generate_content", None, {})
        self.assertIsNotNone(self.ctx.jobs.claim(("generate_content",)))
        self.assertEqual(self.ctx.jobs.recover_stuck(), 1)
        self.assertEqual(self.ctx.db.one("SELECT status FROM jobs")["status"], "queued")

    def test_background_workers_do_the_whole_pipeline_by_themselves(self):
        rt = Runtime(self.ctx)
        rt.start()
        try:
            pid = self.ctx.posts.create(self.owner, title="Auto", brief="Drink water. Stay hydrated.", auto_render=True)
            deadline = time.time() + 60
            state = ""
            while time.time() < deadline:
                state = self.ctx.posts.get(self.owner, pid)["state"]
                if state == "READY_FOR_REVIEW":
                    break
                time.sleep(0.5)
            self.assertEqual(state, "READY_FOR_REVIEW")
            time.sleep(1.2)
            self.login()  # the worker heartbeats are visible on the state screen
            data = self.client.get("/api/state").get_json()
            self.assertTrue(data["workers_alive"])
        finally:
            rt.stop()


class LiveServerTests(AppCase):
    def setUp(self):
        super().setUp()
        self.server = make_server("127.0.0.1", 0, self.app, threaded=True)
        self.port = self.server.server_port
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        super().tearDown()

    def _login_cookie(self):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("GET", "/login")
        r = c.getresponse(); page = r.read().decode()
        cookie = r.getheader("Set-Cookie").split(";")[0]
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        body = f"username=owner&password={PASSWORD.replace(' ', '+')}&csrf_token={token}"
        c.request("POST", "/login", body=body, headers={"Cookie": cookie, "Content-Type": "application/x-www-form-urlencoded"})
        r = c.getresponse(); r.read()
        self.assertEqual(r.status, 302)
        return r.getheader("Set-Cookie").split(";")[0]

    def test_events_arrive_live_over_the_stream(self):
        cookie = self._login_cookie()
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/api/events", headers={"Cookie": cookie})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        self.assertIn("text/event-stream", resp.getheader("Content-Type"))
        got = []

        def reader():
            for raw in iter(lambda: resp.fp.readline(), b""):
                got.append(raw.decode())
                if any("event: activity" in g for g in got) and any("Live check" in g for g in got):
                    return
        t = threading.Thread(target=reader, daemon=True)
        t.start()
        time.sleep(0.5)
        self.ctx.activity.log(self.owner, "Live check", "info")
        t.join(timeout=5)
        text = "".join(got)
        self.assertIn("event: hello", text)
        self.assertIn("Live check", text)
        conn.close()

    def test_stream_needs_login(self):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("GET", "/api/events")
        self.assertEqual(c.getresponse().status, 401)


class PublicMediaTests(AppCase):
    settings_overrides = dict(public_media_base_url="https://media.example.com")

    def test_only_valid_short_lived_links_are_served(self):
        pid = self.ready_post()
        a = self.ctx.posts.assets(pid)[0]
        client = create_public_app(self.ctx.db, self.settings).test_client()
        url = PublicLinks(self.ctx.db, self.settings).create(a["id"], a["ready_key"])
        path = url[len("https://media.example.com"):]
        r = client.get(path)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, "video/mp4")
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(client.get("/m/wrongtoken/x.mp4").status_code, 404)
        self.assertEqual(client.get("/").status_code, 404)
        self.assertEqual(client.get("/api/posts").status_code, 404)  # the dashboard is not reachable here
        self.ctx.db.execute("UPDATE public_links SET expires_at='2000-01-01T00:00:00+00:00'")
        self.assertEqual(client.get(path).status_code, 404)


if __name__ == "__main__":
    unittest.main()
