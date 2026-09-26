import unittest

from app import create_app
from app.config import ConfigError
from tests.helpers import AppCase, make_settings, PASSWORD


class SecurityTests(AppCase):
    def test_pages_and_api_need_login(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers["Location"])
        for path in ("/api/state", "/api/posts", "/api/events", "/api/activity", "/api/briefing"):
            self.assertEqual(self.client.get(path).status_code, 401, path)

    def test_login_flow_and_wrong_password(self):
        page = self.client.get("/login").get_data(as_text=True)
        import re
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        bad = self.client.post("/login", data={"username": "owner", "password": "nope", "csrf_token": token})
        self.assertEqual(bad.status_code, 401)
        self.assertNotIn("Traceback", bad.get_data(as_text=True))
        no_csrf = self.client.post("/login", data={"username": "owner", "password": PASSWORD})
        self.assertEqual(no_csrf.status_code, 403)
        self.login()
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_csrf_required_for_changes(self):
        self.login()
        r = self.client.post("/api/posts", json={"title": "x", "brief": "y"})
        self.assertEqual(r.status_code, 403)
        r = self.api("POST", "/api/posts", json={"title": "x", "brief": "y", "media_type": "REEL"})
        self.assertEqual(r.status_code, 201)

    def test_security_headers_and_no_open_cors(self):
        r = self.client.get("/login", headers={"Origin": "https://evil.example"})
        self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"])
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r.headers["X-Frame-Options"], "DENY")
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)
        self.assertIn("microphone=(self)", r.headers["Permissions-Policy"])

    def test_host_header_rebinding_blocked(self):
        self.assertEqual(self.client.get("/health", headers={"Host": "evil.example.com"}).status_code, 400)
        self.assertEqual(self.client.get("/health", headers={"Host": "localhost:5057"}).status_code, 200)
        self.assertEqual(self.client.get("/health", headers={"Host": "192.168.1.20:5057"}).status_code, 200)

    def test_login_rate_limit(self):
        import re
        page = self.client.get("/login").get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        codes = [self.client.post("/login", data={"username": "owner", "password": "wrong", "csrf_token": token}).status_code for _ in range(10)]
        self.assertEqual(codes[-1], 429)

    def test_errors_are_generic(self):
        @self.app.get("/boom")
        def boom():
            raise RuntimeError("secret internal detail /etc/passwd")
        r = self.client.get("/boom")
        self.assertEqual(r.status_code, 500)
        body = r.get_data(as_text=True)
        self.assertNotIn("Traceback", body)
        self.assertNotIn("secret internal detail", body)

    def test_data_is_isolated_between_users(self):
        self.login()
        pid = self.api("POST", "/api/posts", json={"title": "mine", "brief": "x"}).get_json()["id"]
        db = self.ctx.db
        db.execute("INSERT INTO users(username,password_hash,created_at) VALUES('other','x','2026-01-01T00:00:00')")
        other = db.one("SELECT id FROM users WHERE username='other'")["id"]
        from app.services import ServiceError
        with self.assertRaises(ServiceError):
            self.ctx.posts.get(other, pid)
        self.assertEqual(self.ctx.posts.list(other), [])

    def test_agent_token_can_create_but_not_approve_or_publish(self):
        settings = make_settings(self.tmp + "/agent", agent_api_token="t" * 40)
        app = create_app(settings)
        c = app.test_client()
        self.assertEqual(c.post("/api/agent/posts", json={"title": "a", "brief": "b"}).status_code, 401)
        h = {"Authorization": "Bearer " + "t" * 40}
        r = c.post("/api/agent/posts", json={"title": "a", "brief": "b"}, headers=h)
        self.assertEqual(r.status_code, 201)
        pid = r.get_json()["id"]
        self.assertIn(c.post(f"/api/agent/posts/{pid}/approve", headers=h).status_code, (404, 405))
        self.assertIn(c.post(f"/api/agent/posts/{pid}/publish", headers=h).status_code, (404, 405))
        self.assertEqual(c.get("/api/agent/status", headers={"Authorization": "Bearer wrong"}).status_code, 401)


class ConfigTests(unittest.TestCase):
    def test_refuses_to_start_unsafe(self):
        import tempfile
        d = tempfile.mkdtemp()
        with self.assertRaises(ConfigError):
            create_app(make_settings(d, secret_key=""))
        with self.assertRaises(ConfigError):
            create_app(make_settings(d, admin_password_hash=""))
        with self.assertRaises(ConfigError):
            create_app(make_settings(d, debug=True, env="production"))
        with self.assertRaises(ConfigError):
            create_app(make_settings(d, allowed_origins=("*",)))
        with self.assertRaises(ConfigError):
            create_app(make_settings(d, public_media_base_url="http://insecure.example.com"))


if __name__ == "__main__":
    unittest.main()
