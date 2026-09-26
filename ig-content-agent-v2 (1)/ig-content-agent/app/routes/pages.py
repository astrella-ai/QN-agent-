from __future__ import annotations

from flask import Blueprint, current_app, jsonify, make_response, render_template, send_from_directory

from ..security import csrf_token, login_required

bp = Blueprint("pages", __name__)

MANIFEST = {
    "name": "IG Content Agent", "short_name": "IG Agent", "start_url": "/", "scope": "/", "display": "standalone",
    "background_color": "#1B2430", "theme_color": "#1B2430", "description": "Make, review and publish Instagram content.",
    "icons": [
        {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/static/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}


@bp.get("/")
@login_required
def index():
    ctx = current_app.extensions["ctx"]
    return render_template("app.html", csrf=csrf_token(), brand=ctx.settings.brand_name or "IG Content Agent")


@bp.get("/health")
def health():
    return jsonify(ok=True)


@bp.get("/manifest.webmanifest")
def manifest():
    resp = make_response(jsonify(MANIFEST))
    resp.mimetype = "application/manifest+json"
    return resp


@bp.get("/sw.js")
def service_worker():
    resp = make_response(send_from_directory(current_app.static_folder, "sw.js", mimetype="text/javascript"))
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp
