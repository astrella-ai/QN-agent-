"""Authentication, CSRF, rate limiting, host checks and security headers."""
from __future__ import annotations

import hmac
import ipaddress
import secrets
import socket
import threading
import time
from functools import wraps

from flask import abort, current_app, g, jsonify, redirect, request, session, url_for
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        return check_password_hash(stored_hash, password)
    except Exception:
        return False


class RateLimiter:
    """Simple in-memory sliding window. Enough for one owner; resets on restart."""

    def __init__(self):
        self._hits: dict = {}
        self._lock = threading.Lock()

    def hit(self, bucket: str, key: str, limit: int, window: int) -> bool:
        """Record a hit. Returns True if allowed, False if over the limit."""
        now = time.monotonic()
        k = f"{bucket}:{key}"
        with self._lock:
            arr = [t for t in self._hits.get(k, []) if now - t < window]
            allowed = len(arr) < limit
            if allowed:
                arr.append(now)
            self._hits[k] = arr
            return allowed

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def client_ip() -> str:
    return request.remote_addr or "unknown"


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def host_allowed(host_header: str, settings) -> bool:
    """Block DNS-rebinding: accept localhost, IP literals, this machine's name, and ALLOWED_HOSTS."""
    host = (host_header or "").strip().lower()
    if host.startswith("["):  # [::1]:5057
        name = host.split("]")[0] + "]"
    else:
        name = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    if name in ("localhost", "127.0.0.1", "[::1]"):
        return True
    if _is_ip_literal(name):
        return True
    allowed = {h.lower() for h in settings.allowed_hosts}
    try:
        allowed.add(socket.gethostname().lower())
    except OSError:
        pass
    return name in allowed


def csrf_token() -> str:
    tok = session.get("csrf")
    if not tok:
        tok = secrets.token_urlsafe(32)
        session["csrf"] = tok
    return tok


def _csrf_ok() -> bool:
    sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
    want = session.get("csrf", "")
    return bool(want) and bool(sent) and hmac.compare_digest(sent, want)


def current_owner_id() -> int | None:
    return session.get("uid")


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not current_owner_id():
            if request.path.startswith("/api/"):
                return jsonify(error="Sign in required."), 401
            return redirect(url_for("auth.login_page"))
        g.owner_id = current_owner_id()
        return fn(*a, **kw)
    return wrapper


def agent_token_required(fn):
    """Separate credential for the automation agent. It can never approve or publish."""
    @wraps(fn)
    def wrapper(*a, **kw):
        settings = current_app.extensions["ctx"].settings
        sent = request.headers.get("Authorization", "")
        want = settings.agent_api_token
        if not want or not sent.startswith("Bearer ") or not hmac.compare_digest(sent[7:], want):
            return jsonify(error="Invalid agent token."), 401
        ctx = current_app.extensions["ctx"]
        if not ctx.limiter.hit("agent", client_ip(), 120, 60):
            return jsonify(error="Too many requests."), 429
        row = ctx.db.one("SELECT id FROM users ORDER BY id LIMIT 1")
        if not row:
            return jsonify(error="No owner account."), 500
        g.owner_id = row["id"]
        g.is_agent = True
        return fn(*a, **kw)
    return wrapper


def init_security(app) -> None:
    ctx = app.extensions["ctx"]
    settings = ctx.settings

    @app.before_request
    def _guard():
        if not host_allowed(request.host, settings):
            abort(400)
        if request.method in MUTATING and not request.path.startswith("/api/agent/"):
            signed_out_api = request.path.startswith("/api/") and not session.get("uid")
            if not signed_out_api and not _csrf_ok():  # signed-out API calls get a clean 401 from login_required
                if request.path.startswith("/api/"):
                    return jsonify(error="Your session expired. Reload the page and try again."), 403
                abort(403)

    @app.after_request
    def _headers(resp):
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; "
            "media-src 'self' blob:; connect-src 'self'; manifest-src 'self'; worker-src 'self'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'")
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Permissions-Policy"] = "microphone=(self), camera=(), geolocation=(), payment=()"
        resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if request.is_secure or settings.cookie_secure:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path.startswith("/api/") or resp.mimetype == "text/html":
            resp.headers["Cache-Control"] = "no-store"
        origin = request.headers.get("Origin")
        if origin and origin in settings.allowed_origins:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-CSRF-Token"
            resp.headers["Vary"] = "Origin"
        return resp

    @app.errorhandler(400)
    def _e400(e):
        return _error_page(400, "That request was not valid.")

    @app.errorhandler(403)
    def _e403(e):
        return _error_page(403, "That action was not allowed. Reload the page and try again.")

    @app.errorhandler(404)
    def _e404(e):
        return _error_page(404, "Not found.")

    @app.errorhandler(413)
    def _e413(e):
        return _error_page(413, f"That file is too large. The limit is {settings.max_upload_mb} MB.")

    @app.errorhandler(Exception)
    def _e500(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return _error_page(e.code or 500, e.description or "Error")
        app.logger.exception("Unhandled error")  # details go to the log only
        return _error_page(500, "Something went wrong on the server. The details are in the server log.")


def _error_page(code: int, message: str):
    if request.path.startswith("/api/"):
        return jsonify(error=message), code
    return (f"<!doctype html><meta charset=utf-8><title>Error {code}</title>"
            f"<body style='font-family:system-ui;padding:2rem'><h1>Error {code}</h1>"
            f"<p>{escape(message)}</p><p><a href='/'>Back to the dashboard</a></p>"), code
