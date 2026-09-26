from __future__ import annotations

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from ..security import client_ip, csrf_token, hash_password, verify_password

bp = Blueprint("auth", __name__)
_DUMMY = hash_password("not-a-real-password")


@bp.get("/login")
def login_page():
    if session.get("uid"):
        return redirect("/")
    return render_template("login.html", csrf=csrf_token(), error=request.args.get("e", ""))


@bp.post("/login")
def login_submit():
    ctx = current_app.extensions["ctx"]
    ip = client_ip()
    username = (request.form.get("username") or "").strip()[:80]
    if not (ctx.limiter.hit("login-ip", ip, 8, 600) and ctx.limiter.hit("login-user", username.lower(), 8, 600)):
        return render_template("login.html", csrf=csrf_token(), error="Too many attempts. Wait ten minutes and try again."), 429
    row = ctx.db.one("SELECT id, password_hash FROM users WHERE username=?", (username,))
    ok = verify_password(row["password_hash"] if row else _DUMMY, request.form.get("password") or "")
    if not (row and ok):
        ctx.log.warning("Failed login from %s", ip)
        return render_template("login.html", csrf=csrf_token(), error="That username or password is not right."), 401
    session.clear()
    session["uid"] = row["id"]
    session.permanent = True
    csrf_token()
    ctx.log.info("Login from %s", ip)
    return redirect("/")


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))
