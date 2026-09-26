import io
import json

from werkzeug.datastructures import FileStorage

from app.media import MediaError, safe_child, sniff_kind
from app.pipeline import PublishRefused
from app.services import ServiceError
from tests.helpers import AppCase, make_image, make_video


class PostFlowTests(AppCase):
    def test_brief_becomes_reviewable_post_without_any_ai_key(self):
        pid = self.ctx.posts.create(self.owner, title="Sleep", brief="Sleep well. Keep the room cool.", auto_render=True)
        self.assertEqual(self.ctx.posts.get(self.owner, pid)["state"], "RENDERING")
        self.run_jobs()
        p = self.ctx.posts.get(self.owner, pid)
        self.assertEqual(p["state"], "READY_FOR_REVIEW")
        self.assertTrue(p["caption"])
        self.assertEqual(p["assets"][0]["status"], "ready")
        self.assertEqual((p["assets"][0]["width"], p["assets"][0]["height"]), (1080, 1920))
        self.assertTrue(p["can_approve"])

    def test_approval_binds_to_exact_content(self):
        pid = self.ready_post()
        self.ctx.posts.approve(self.owner, pid)
        self.assertEqual(self.ctx.posts.get(self.owner, pid)["state"], "APPROVED")
        self.ctx.posts.update(self.owner, pid, {"caption": "A different caption"})
        p = self.ctx.posts.get(self.owner, pid)
        self.assertNotEqual(p["state"], "APPROVED")
        self.assertFalse(p["approved"])
        with self.assertRaises(ServiceError):
            self.ctx.posts.request_publish(self.owner, pid)

    def test_cannot_publish_without_approval(self):
        pid = self.ready_post()
        with self.assertRaises(ServiceError):
            self.ctx.posts.request_publish(self.owner, pid)
        # even a forced job cannot publish an unapproved post
        self.ctx.jobs.enqueue(self.owner, "publish", pid)
        self.run_jobs(("publish",))
        self.assertNotIn(self.ctx.posts.get(self.owner, pid)["state"], ("PUBLISHED", "DRY_RUN_COMPLETE"))
        self.assertEqual(self.ctx.db.one("SELECT COUNT(*) c FROM publish_attempts WHERE mode='live'")["c"], 0)

    def test_dry_run_publish_completes_and_posts_nothing(self):
        pid = self.ready_post()
        self.ctx.posts.approve(self.owner, pid)
        self.ctx.posts.request_publish(self.owner, pid)
        self.assertEqual(self.ctx.posts.get(self.owner, pid)["state"], "PUBLISHING")
        self.run_jobs(("publish",))
        p = self.ctx.posts.get(self.owner, pid)
        self.assertEqual(p["state"], "DRY_RUN_COMPLETE")
        row = self.ctx.db.one("SELECT mode,status FROM publish_attempts WHERE post_id=?", (pid,))
        self.assertEqual((row["mode"], row["status"]), ("dry_run", "ok"))
        self.assertEqual(p["permalink"], "")

    def test_file_changed_after_approval_is_refused(self):
        pid = self.ready_post()
        self.ctx.posts.approve(self.owner, pid)
        a = self.ctx.posts.assets(pid)[0]
        with open(safe_child(self.settings.media_dir, a["ready_key"]), "ab") as f:
            f.write(b"tampered")
        self.ctx.posts.request_publish(self.owner, pid)
        self.run_jobs(("publish",))
        p = self.ctx.posts.get(self.owner, pid)
        self.assertEqual(p["state"], "FAILED")
        self.assertIn("changed", p["error"].lower())

    def test_validation(self):
        with self.assertRaises(ServiceError):
            self.ctx.posts.create(self.owner, title="", brief="")
        with self.assertRaises(ServiceError):
            self.ctx.posts.create(self.owner, title="x", media_type="TIKTOK")
        pid = self.ctx.posts.create(self.owner, title="x", brief="y")
        with self.assertRaises(ServiceError):
            self.ctx.posts.update(self.owner, pid, {"caption": "a" * 2201})
        with self.assertRaises(ServiceError):
            self.ctx.posts.update(self.owner, pid, {"hashtags": "#ok #not valid!"})
        with self.assertRaises(ServiceError):
            self.ctx.posts.update(self.owner, pid, {"hashtags": " ".join(f"#t{i}" for i in range(31))})
        out = self.ctx.posts.update(self.owner, pid, {"hashtags": "sleep, #Sleep  health"})
        self.assertEqual(out["hashtags"], "#sleep #health")
        with self.assertRaises(ServiceError):
            self.ctx.posts.update(self.owner, pid, {"scheduled_for": "2001-01-01T00:00:00+00:00"})

    def test_html_in_caption_is_stored_as_plain_text(self):
        pid = self.ctx.posts.create(self.owner, title="x", brief="y")
        self.ctx.posts.update(self.owner, pid, {"caption": "<script>alert(1)</script>"})
        self.assertEqual(self.ctx.posts.get(self.owner, pid)["caption"], "<script>alert(1)</script>")
        js = open("app/static/app.js", encoding="utf-8").read()
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("insertAdjacentHTML", js)


class UploadTests(AppCase):
    def fs(self, data: bytes, name: str):
        return FileStorage(stream=io.BytesIO(data), filename=name)

    def test_fake_video_is_rejected_by_content(self):
        pid = self.ctx.posts.create(self.owner, title="x", brief="y")
        with self.assertRaises(MediaError):
            self.ctx.media.save_upload(self.owner, pid, self.fs(b"MZ\x90\x00 this is a program", "cute.mp4"))
        with self.assertRaises(MediaError):
            self.ctx.media.save_upload(self.owner, pid, self.fs(b"<html></html>", "x.exe"))
        self.assertEqual(self.ctx.posts.assets(pid), [])

    def test_extension_must_match_content(self):
        pid = self.ctx.posts.create(self.owner, title="x", brief="y", media_type="STORY")
        img = make_image(self.tmp + "/a.png")
        with self.assertRaises(MediaError):
            self.ctx.media.save_upload(self.owner, pid, self.fs(img.read_bytes(), "photo.mp4"))

    def test_size_limit(self):
        s = self.settings
        from dataclasses import replace
        self.ctx.media.s = replace(s, max_upload_mb=1)
        pid = self.ctx.posts.create(self.owner, title="x", brief="y")
        with self.assertRaises(MediaError):
            self.ctx.media.save_upload(self.owner, pid, self.fs(b"\x00\x00\x00\x18ftypmp42" + b"0" * (2 * 1024 * 1024), "big.mp4"))

    def test_real_video_upload_is_normalized(self):
        pid = self.ctx.posts.create(self.owner, title="clip", brief="", caption="Nice clip")
        v = make_video(self.tmp + "/in.mp4", seconds=2, size="1280x720")
        self.ctx.media.save_upload(self.owner, pid, self.fs(v.read_bytes(), "my clip.mp4"))
        self.assertEqual(self.ctx.posts.get(self.owner, pid)["state"], "RENDERING")
        self.run_jobs()
        p = self.ctx.posts.get(self.owner, pid)
        self.assertEqual(p["state"], "READY_FOR_REVIEW")
        self.assertEqual((p["assets"][0]["width"], p["assets"][0]["height"]), (1080, 1920))
        # the stored name is random, never the client's
        a = self.ctx.posts.assets(pid)[0]
        self.assertNotIn("clip", a["storage_key"])

    def test_image_upload_becomes_jpeg(self):
        pid = self.ctx.posts.create(self.owner, title="pic", brief="", caption="Pic", media_type="IMAGE")
        img = make_image(self.tmp + "/a.png", size="1000x400")
        self.ctx.media.save_upload(self.owner, pid, self.fs(img.read_bytes(), "a.png"))
        self.run_jobs()
        a = self.ctx.posts.assets(pid)[0]
        self.assertTrue(a["ready_key"].endswith(".jpg"))
        self.assertGreaterEqual(a["width"] / a["height"], 0.79)
        self.assertLessEqual(a["width"] / a["height"], 1.92)

    def test_reel_rejects_a_picture_and_carousel_limit(self):
        pid = self.ctx.posts.create(self.owner, title="x", brief="y")
        img = make_image(self.tmp + "/a.png")
        with self.assertRaises(MediaError):
            self.ctx.media.save_upload(self.owner, pid, self.fs(img.read_bytes(), "a.png"))
        cid = self.ctx.posts.create(self.owner, title="c", brief="", caption="c", media_type="CAROUSEL")
        for _ in range(10):
            self.ctx.media.save_upload(self.owner, cid, self.fs(img.read_bytes(), "a.png"))
        with self.assertRaises(MediaError):
            self.ctx.media.save_upload(self.owner, cid, self.fs(img.read_bytes(), "a.png"))

    def test_path_traversal_blocked(self):
        with self.assertRaises(MediaError):
            safe_child(self.settings.media_dir, "../../etc/passwd")

    def test_sniff(self):
        self.assertEqual(sniff_kind(b"\xff\xd8\xff\xe0" + b"0" * 20), "image")
        self.assertEqual(sniff_kind(b"\x00\x00\x00\x18ftypisom"), "video")
        self.assertIsNone(sniff_kind(b"MZ\x90\x00"))

    def test_upload_via_api_needs_login_and_csrf(self):
        pid = self.ctx.posts.create(self.owner, title="x", brief="y")
        r = self.client.post(f"/api/posts/{pid}/assets", data={"file": (io.BytesIO(b"x"), "a.mp4")})
        self.assertEqual(r.status_code, 401)
        self.login()
        r = self.client.post(f"/api/posts/{pid}/assets", data={"file": (io.BytesIO(b"x"), "a.mp4")})
        self.assertEqual(r.status_code, 403)
        v = make_video(self.tmp + "/in.mp4", seconds=1)
        r = self.api("POST", f"/api/posts/{pid}/assets", data={"file": (io.BytesIO(v.read_bytes()), "in.mp4")}, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 201, r.get_data(as_text=True))
        r = self.api("POST", f"/api/posts/{pid}/assets", data={"file": (io.BytesIO(b"not a video at all"), "in.mp4")}, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)
        self.assertIn("not a real", r.get_json()["error"])


if __name__ == "__main__":
    import unittest
    unittest.main()
