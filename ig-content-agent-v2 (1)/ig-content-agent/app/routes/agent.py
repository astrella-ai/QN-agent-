"""API for the owner's automation agent. It has its own token and can never approve or publish."""
from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from ..media import MediaError
from ..security import agent_token_required
from ..services import ServiceError

bp = Blueprint("agent", __name__, url_prefix="/api/agent")


def C():
    return current_app.extensions["ctx"]


@bp.errorhandler(ServiceError)
def _se(e):
    return jsonify(error=e.message), e.status


@bp.errorhandler(MediaError)
def _me(e):
    return jsonify(error=str(e)), 400


@bp.get("/status")  # permission level: Observe
@agent_token_required
def status():
    return jsonify(counts=C().posts.counts(g.owner_id), dry_run=C().settings.dry_run)


@bp.post("/posts")  # permission level: Create
@agent_token_required
def create():
    d = request.get_json(silent=True) or {}
    mt = str(d.get("media_type", "REEL")).upper()
    pid = C().posts.create(g.owner_id, title=d.get("title", ""), brief=d.get("brief", ""), media_type=mt,
                           auto_render=bool(d.get("auto_render", mt in ("REEL", "STORY"))))
    C().activity.log(g.owner_id, f"The automation agent created post {pid}.", "info", pid, "Create")
    return jsonify(C().posts.get(g.owner_id, pid)), 201


@bp.get("/posts/<int:pid>")  # permission level: Observe
@agent_token_required
def get_post(pid):
    return jsonify(C().posts.get(g.owner_id, pid))
