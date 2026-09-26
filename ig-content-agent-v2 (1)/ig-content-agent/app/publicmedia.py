"""A tiny separate web server that ONLY serves short-lived media links.

Instagram downloads media from a public URL. Point your tunnel at this port, not at the dashboard,
so the dashboard is never exposed to the internet.
"""
from __future__ import annotations

import mimetypes
import secrets
import threading
from datetime import datetime, timedelta, timezone

from flask import Flask, abort, send_file
from werkzeug.serving import make_server

from .db import Database, now_iso, parse_iso
from .media import safe_child

TTL_MINUTES = 30


class PublicLinks:
    def __init__(self, db: Database, settings):
        self.db, self.s = db, settings

    def create(self, asset_id: int, filename: str) -> str:
        token = secrets.token_urlsafe(24)
        exp = (datetime.now(timezone.utc) + timedelta(minutes=TTL_MINUTES)).isoformat(timespec="seconds")
        self.db.execute("INSERT INTO public_links(token,asset_id,expires_at) VALUES(?,?,?)", (token, asset_id, exp))
        return f"{self.s.public_media_base_url}/m/{token}/{filename}"

    def local_url(self, token_url: str) -> str:
        path = token_url[len(self.s.public_media_base_url):]
        return f"http://127.0.0.1:{self.s.public_media_port}{path}"

    def revoke_asset(self, asset_id: int) -> None:
        self.db.execute("DELETE FROM public_links WHERE asset_id=?", (asset_id,))

    def purge_expired(self) -> None:
        self.db.execute("DELETE FROM public_links WHERE expires_at < ?", (now_iso(),))


def create_public_app(db: Database, settings) -> Flask:
    app = Flask("public_media")

    @app.get("/m/<token>/<name>")
    def serve(token, name):
        row = db.one("SELECT p.asset_id, p.expires_at, a.ready_key FROM public_links p JOIN assets a ON a.id=p.asset_id "
                     "WHERE p.token=?", (token,))
        if not row or parse_iso(row["expires_at"]) < datetime.now(timezone.utc) or not row["ready_key"]:
            abort(404)
        path = safe_child(settings.media_dir, row["ready_key"])
        if not path.exists():
            abort(404)
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        resp = send_file(path, mimetype=mime, conditional=True)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.errorhandler(Exception)
    def any_error(e):
        return ("Not found", 404)

    return app


class PublicServer:
    def __init__(self, db, settings):
        self.app = create_public_app(db, settings)
        self.s = settings
        self._server = None
        self._thread = None

    def start(self) -> None:
        self._server = make_server("127.0.0.1", self.s.public_media_port, self.app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, name="public-media", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
