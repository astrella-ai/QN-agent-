"""IG Content Agent: a local, approval-gated Instagram content assistant."""
from __future__ import annotations

import logging
import threading
from logging.handlers import RotatingFileHandler
from types import SimpleNamespace

from flask import Flask

from .assistant import Assistant
from .config import Settings
from .db import Database, now_iso
from .events import ActivityLog, EventBus
from .llm import build_provider
from .media import Ffmpeg
from .notify import Notifier
from .pipeline import JobRunner, MediaService, Runtime
from .publicmedia import PublicLinks
from .publisher import Publisher
from .security import RateLimiter, hash_password, init_security
from .services import JobQueue, PostService

__version__ = "0.2.0"


class RedactFilter(logging.Filter):
    """Masks configured secrets if they ever reach a log line."""

    def __init__(self, secrets_):
        super().__init__()
        self.secrets = [s for s in secrets_ if s and len(s) >= 8]

    def filter(self, record):
        msg = record.getMessage()
        for s in self.secrets:
            msg = msg.replace(s, "[hidden]")
        record.msg, record.args = msg, ()
        return True


def setup_logging(settings: Settings) -> logging.Logger:
    log = logging.getLogger("igagent")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    redact = RedactFilter([settings.secret_key, settings.llm_api_key, settings.ig_access_token, settings.agent_api_token,
                           settings.telegram_bot_token, settings.admin_password_hash])
    handlers = [logging.StreamHandler()]
    try:
        settings.logs_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(settings.logs_dir / "app.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"))
    except OSError:
        pass
    for h in handlers:
        h.setFormatter(fmt)
        h.addFilter(redact)
        log.addHandler(h)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # request lines can contain media tokens
    return log


def build_context(settings: Settings) -> SimpleNamespace:
    settings.ensure_dirs()
    c = SimpleNamespace(settings=settings)
    c.log = setup_logging(settings)
    c.db = Database(settings.db_path)
    c.bus = EventBus()
    c.activity = ActivityLog(c.db, c.bus)
    c.jobs = JobQueue(c.db)
    c.notifier = Notifier(settings)
    c.limiter = RateLimiter()
    c.llm = build_provider(settings)
    c.ff = Ffmpeg(settings.ffmpeg_path, settings.ffprobe_path)
    c.posts = PostService(c.db, settings, c.bus, c.activity, c.jobs, c.notifier)
    c.media = MediaService(settings, c.db, c.posts, c.jobs, c.activity, c.ff)
    c.public_links = PublicLinks(c.db, settings)
    c.runner = JobRunner(c)
    c.publisher = Publisher(c)
    c.assistant = Assistant(c)
    c.runtime = Runtime(c)
    return c


def ensure_owner(ctx) -> int:
    """The single owner account follows .env, so changing the password there takes effect on restart."""
    s = ctx.settings
    row = ctx.db.one("SELECT id FROM users ORDER BY id LIMIT 1")
    if row:
        ctx.db.execute("UPDATE users SET username=?, password_hash=? WHERE id=?", (s.admin_username, s.admin_password_hash, row["id"]))
        return row["id"]
    return ctx.db.execute("INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)",
                          (s.admin_username, s.admin_password_hash, now_iso())).lastrowid


def create_app(settings: Settings, start_workers: bool = False) -> Flask:
    settings.validate()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=settings.cookie_secure,
        SESSION_COOKIE_NAME="igagent", PERMANENT_SESSION_LIFETIME=7 * 24 * 3600,
        MAX_CONTENT_LENGTH=(settings.max_upload_mb * 10 + 5) * 1024 * 1024,  # up to 10 files in one request
        JSON_AS_ASCII=False, TEMPLATES_AUTO_RELOAD=False)
    app.debug = False
    ctx = build_context(settings)
    ensure_owner(ctx)
    app.extensions["ctx"] = ctx
    init_security(app)

    from .routes import agent as agent_routes, api as api_routes, auth as auth_routes, pages as page_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(page_routes.bp)
    app.register_blueprint(api_routes.bp)
    app.register_blueprint(agent_routes.bp)
    if start_workers:
        ctx.runtime.start()
    return app
