import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.config import Settings  # noqa: E402
from app.security import hash_password  # noqa: E402

PASSWORD = "correct horse battery"
PW_HASH = hash_password(PASSWORD)


def make_settings(tmp, **kw):
    base = dict(secret_key="k" * 40, admin_username="owner", admin_password_hash=PW_HASH, data_dir=Path(tmp),
                workers=False, dry_run=True)
    base.update(kw)
    return Settings(**base)


def make_video(path, seconds=2, size="640x360", audio=True):
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=24:duration={seconds}"]
    if audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-c:a", "aac", "-shortest"]
    args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
    subprocess.run(args, check=True)
    return Path(path)


def make_image(path, size="800x600", fmt="png"):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=1",
                    "-frames:v", "1", str(path)], check=True)
    return Path(path)


class AppCase(unittest.TestCase):
    settings_overrides: dict = {}

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="igtest-")
        self.settings = make_settings(self.tmp, **self.settings_overrides)
        self.app = create_app(self.settings)
        self.ctx = self.app.extensions["ctx"]
        self.client = self.app.test_client()
        self.owner = self.ctx.db.one("SELECT id FROM users ORDER BY id LIMIT 1")["id"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def login(self, client=None):
        c = client or self.client
        page = c.get("/login").get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        r = c.post("/login", data={"username": "owner", "password": PASSWORD, "csrf_token": token})
        assert r.status_code == 302, r.status_code
        with c.session_transaction() as s:
            self.csrf = s["csrf"]
        return c

    def api(self, method, path, **kw):
        headers = kw.pop("headers", {})
        headers["X-CSRF-Token"] = self.csrf
        return self.client.open(path, method=method, headers=headers, **kw)

    def run_jobs(self, kinds=("generate_content", "normalize", "render_template", "publish"), limit=20):
        n = 0
        while n < limit and self.ctx.runner.run_one(kinds):
            n += 1
        return n

    def ready_post(self, **kw):
        """A post with a rendered video and a caption, ready for review."""
        pid = self.ctx.posts.create(self.owner, title=kw.get("title", "Sleep tips"), brief=kw.get("brief", "Sleep well. Keep the room cool."),
                                    media_type=kw.get("media_type", "REEL"), auto_render=True)
        self.run_jobs()
        return pid
