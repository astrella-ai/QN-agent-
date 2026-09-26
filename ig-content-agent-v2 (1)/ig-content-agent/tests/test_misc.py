import json
import logging
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import manage
from app import RedactFilter
from app import llm as llmmod
from app.config import Settings, parse_dotenv
from app.media import script_to_lines
from app.notify import Notifier, clean_speech, in_quiet_hours
from tests.helpers import make_settings


class ManageTests(unittest.TestCase):
    def test_env_editing(self):
        t = "A=1\nSECRET_KEY=\nB=2\n"
        self.assertEqual(manage.set_env_value(t, "SECRET_KEY", "abc"), "A=1\nSECRET_KEY=abc\nB=2\n")
        self.assertTrue(manage.set_env_value(t, "NEW", "x").endswith("NEW=x\n"))
        self.assertEqual(parse_dotenv("A=1\n#c\nB='two'\n")["B"], "two")

    def test_init_writes_a_hash_never_the_password(self):
        d = Path(tempfile.mkdtemp())
        (d / ".env.example").write_text((manage.ROOT / ".env.example").read_text())
        with mock.patch.object(manage, "ROOT", d), mock.patch.dict("os.environ", {"IGAGENT_PASSWORD": "a-long-secret-password"}):
            self.assertEqual(manage.cmd_init(mock.Mock(username="boss")), 0)
            text = (d / ".env").read_text()
            self.assertNotIn("a-long-secret-password", text)
            env = parse_dotenv(text)
            self.assertEqual(len(env["SECRET_KEY"]), 64)
            self.assertEqual(env["ADMIN_USERNAME"], "boss")
            self.assertTrue(env["ADMIN_PASSWORD_HASH"].startswith(("scrypt:", "pbkdf2:")))
            s = Settings.from_env(env)
            s.validate()  # a fresh install passes the safety checks
            self.assertTrue(s.dry_run)  # and starts in dry-run mode
            self.assertEqual(s.host, "127.0.0.1")
            self.assertEqual(manage.cmd_init(mock.Mock(username="x")), 0)  # never overwrites an existing .env
            self.assertEqual((d / ".env").read_text(), text)

    def test_autostart_definitions(self):
        args = manage.windows_task_args(r"C:\Py\pythonw.exe", r"C:\App\manage.py")
        self.assertIn("ONLOGON", args)
        self.assertEqual(args[args.index("/TR") + 1], r'"C:\Py\pythonw.exe" "C:\App\manage.py" run --open')
        self.assertNotIn("--open", manage.windows_task_args("p", "m", False)[args.index("/TR") + 1])
        self.assertIn("RunAtLoad", manage.launchd_plist("/usr/bin/python3", "/x/manage.py"))
        self.assertIn("ExecStart=/usr/bin/python3 /x/manage.py run", manage.systemd_unit("/usr/bin/python3", "/x/manage.py"))

    def test_single_instance_port_check(self):
        import socket
        s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1)
        self.assertTrue(manage.port_in_use("127.0.0.1", s.getsockname()[1]))
        s.close()


class NotifyTests(unittest.TestCase):
    def test_speech_text_goes_through_stdin_never_the_command_line(self):
        calls = []
        n = Notifier(make_settings(tempfile.mkdtemp(), local_tts=True), runner=lambda cmd, **kw: calls.append((cmd, kw)))
        evil = 'hello"; Remove-Item C:\\ -Recurse; "'
        with mock.patch("app.notify.tts_command", return_value=["speak-tool", "--stdin"]):
            n.speak_local(evil)
            for t in __import__("threading").enumerate():
                if t is not __import__("threading").current_thread() and t.daemon:
                    t.join(timeout=2)
        self.assertEqual(len(calls), 1)
        cmd, kw = calls[0]
        self.assertEqual(cmd, ["speak-tool", "--stdin"])
        self.assertNotIn("Remove-Item", " ".join(cmd))
        self.assertIn(b"Remove-Item", kw["input"])

    def test_quiet_hours_and_cleaning(self):
        self.assertTrue(in_quiet_hours("22-7", datetime(2026, 9, 21, 23)))
        self.assertTrue(in_quiet_hours("22-7", datetime(2026, 9, 21, 3)))
        self.assertFalse(in_quiet_hours("22-7", datetime(2026, 9, 21, 12)))
        self.assertFalse(in_quiet_hours("", datetime(2026, 9, 21, 12)))
        self.assertEqual(clean_speech("a\x00b\n\nc"), "a b c")

    def test_off_by_default(self):
        calls = []
        n = Notifier(make_settings(tempfile.mkdtemp()), runner=lambda *a, **k: calls.append(1))
        n.speak_local("hello")
        self.assertEqual(calls, [])

    def test_telegram_sends_json_body_only_when_configured(self):
        sent = []
        n = Notifier(make_settings(tempfile.mkdtemp(), telegram_bot_token="123:abc", telegram_chat_id="9"), opener=lambda req, timeout=0: sent.append(req))
        n.telegram("Post 3 needs you")
        for t in __import__("threading").enumerate():
            if t.daemon and t is not __import__("threading").current_thread():
                t.join(timeout=2)
        self.assertEqual(len(sent), 1)
        self.assertEqual(json.loads(sent[0].data)["chat_id"], "9")


class LLMTests(unittest.TestCase):
    def fake_urlopen(self, captured, payload):
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return json.dumps(payload).encode()
        def opener(req, timeout=0):
            captured.append(req)
            return R()
        return opener

    def call(self, provider, payload, **kw):
        s = make_settings(tempfile.mkdtemp(), llm_provider=provider, llm_api_key="KEY123456789", **kw)
        prov = llmmod.build_provider(s)
        cap = []
        with mock.patch("urllib.request.urlopen", self.fake_urlopen(cap, payload)):
            out = prov.complete("SYS", [{"role": "user", "content": "hi"}])
        return out, cap[0]

    def test_anthropic_request_shape(self):
        out, req = self.call("anthropic", {"content": [{"type": "text", "text": "hello"}]})
        self.assertEqual(out, "hello")
        self.assertEqual(req.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(req.get_header("X-api-key"), "KEY123456789")
        body = json.loads(req.data)
        self.assertEqual((body["system"], body["messages"][0]["role"]), ("SYS", "user"))

    def test_openai_and_gemini_request_shape(self):
        out, req = self.call("openai", {"choices": [{"message": {"content": "yo"}}]})
        self.assertEqual((out, req.full_url), ("yo", "https://api.openai.com/v1/chat/completions"))
        self.assertEqual(req.get_header("Authorization"), "Bearer KEY123456789")
        out, req = self.call("gemini", {"candidates": [{"content": {"parts": [{"text": "hey"}]}}]})
        self.assertEqual(out, "hey")
        self.assertIn(":generateContent", req.full_url)
        self.assertNotIn("KEY123456789", req.full_url)  # the key is in a header, not the URL
        self.assertEqual(req.get_header("X-goog-api-key"), "KEY123456789")

    def test_local_ollama_needs_no_key(self):
        p = llmmod.build_provider(make_settings(tempfile.mkdtemp(), llm_provider="ollama"))
        self.assertEqual(p.url, "http://localhost:11434/v1/chat/completions")
        self.assertIsNone(llmmod.build_provider(make_settings(tempfile.mkdtemp(), llm_provider="anthropic")))  # no key: offline

    def test_errors_are_friendly_and_never_contain_the_key(self):
        import urllib.error
        def boom(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 401, "no", {}, None)
        prov = llmmod.build_provider(make_settings(tempfile.mkdtemp(), llm_provider="anthropic", llm_api_key="KEY123456789"))
        with mock.patch("urllib.request.urlopen", boom):
            with self.assertRaises(llmmod.LLMError) as cm:
                prov.complete("s", [{"role": "user", "content": "x"}])
        self.assertNotIn("KEY123456789", str(cm.exception))

    def test_content_generation_validates_model_output(self):
        class P:
            name = "p"
            def complete(self, *a, **k):
                return 'Sure: {"caption": "Great post", "hashtags": ["sleep", "no spaces!", ""], "lines": ["One", "Two"]}'
        out = llmmod.generate_content(P(), "brief about sleep")
        self.assertEqual(out["hashtags"], "#sleep #nospaces")
        self.assertEqual(out["lines"], ["One", "Two"])

        class Bad:
            name = "bad"
            def complete(self, *a, **k):
                return "I cannot help"
        self.assertEqual(llmmod.generate_content(Bad(), "Tea is nice. Drink it.")["source"], "offline")


class MiscTests(unittest.TestCase):
    def test_secrets_are_masked_in_logs(self):
        f = RedactFilter(["SUPERSECRETTOKEN123"])
        rec = logging.LogRecord("x", logging.INFO, "", 0, "token is %s", ("SUPERSECRETTOKEN123",), None)
        f.filter(rec)
        self.assertNotIn("SUPERSECRETTOKEN123", rec.getMessage())

    def test_script_to_lines(self):
        lines = script_to_lines("Stop scrolling. Here is a really long sentence that must wrap onto several short lines. Done!")
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(len(part) <= 22 for l in lines for part in l.split("\n")))
        self.assertEqual(script_to_lines(""), [])

    def test_env_example_has_no_real_values(self):
        env = parse_dotenv((Path(manage.ROOT) / ".env.example").read_text())
        for key in ("SECRET_KEY", "ADMIN_PASSWORD_HASH", "IG_ACCESS_TOKEN", "LLM_API_KEY", "AGENT_API_TOKEN", "TELEGRAM_BOT_TOKEN"):
            self.assertEqual(env[key], "", key)
        self.assertEqual(env["DRY_RUN"], "1")
        self.assertEqual(env["HOST"], "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
