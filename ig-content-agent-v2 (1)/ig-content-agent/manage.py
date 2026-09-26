#!/usr/bin/env python3
"""Command line for IG Content Agent.

  python manage.py init                 first-time setup (creates .env with a secret key and your password hash)
  python manage.py doctor               check that everything needed is in place
  python manage.py run [--open]         start the app (workers, live screen, voice, inbox watcher)
  python manage.py install-autostart    start automatically when you sign in to this PC
  python manage.py remove-autostart
  python manage.py set-password         change the sign-in password
  python manage.py agent-token          create a key for your automation agent
"""
from __future__ import annotations

import argparse
import getpass
import os
import platform
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

TASK_NAME = "IGContentAgent"


# ---- .env editing ----------------------------------------------------------------------------------
def set_env_value(text: str, key: str, value: str) -> str:
    line = f"{key}={value}"
    pattern = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    if pattern.search(text):
        return pattern.sub(lambda m: line, text, count=1)
    return text.rstrip("\n") + "\n" + line + "\n"


def write_env(text: str) -> None:
    p = ROOT / ".env"
    p.write_text(text, encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def ask_password() -> str:
    env_pw = os.environ.get("IGAGENT_PASSWORD")  # for scripted setup only
    if env_pw:
        return env_pw
    while True:
        pw = getpass.getpass("Choose a password (at least 10 characters): ")
        if len(pw) < 10:
            print("That is too short.")
            continue
        if pw != getpass.getpass("Type it again: "):
            print("They did not match.")
            continue
        return pw


def local_names() -> list:
    names = {socket.gethostname()}
    return sorted(n for n in names if n)


# ---- commands --------------------------------------------------------------------------------------
def cmd_init(args) -> int:
    from app.security import hash_password
    if (ROOT / ".env").exists():
        print(".env already exists, so nothing was changed. Use 'python manage.py set-password' to change the password.")
        return 0
    username = args.username or (input("Choose a username [owner]: ").strip() if sys.stdin.isatty() else "") or "owner"
    pw = ask_password()
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    text = set_env_value(text, "SECRET_KEY", secrets.token_hex(32))
    text = set_env_value(text, "ADMIN_USERNAME", username)
    text = set_env_value(text, "ADMIN_PASSWORD_HASH", hash_password(pw))
    text = set_env_value(text, "ALLOWED_HOSTS", ",".join(local_names()))
    write_env(text)
    from app.config import Settings
    Settings.from_env().ensure_dirs()
    print("\nSetup done. Your password is stored only as a hash in .env (never commit that file).")
    print("Next: python manage.py doctor   then   python manage.py run --open")
    return 0


def cmd_set_password(args) -> int:
    from app.security import hash_password
    p = ROOT / ".env"
    if not p.exists():
        print("No .env yet. Run: python manage.py init")
        return 1
    write_env(set_env_value(p.read_text(encoding="utf-8"), "ADMIN_PASSWORD_HASH", hash_password(ask_password())))
    print("Password changed. Restart the app for it to take effect.")
    return 0


def cmd_agent_token(args) -> int:
    p = ROOT / ".env"
    if not p.exists():
        print("No .env yet. Run: python manage.py init")
        return 1
    token = secrets.token_urlsafe(32)
    write_env(set_env_value(p.read_text(encoding="utf-8"), "AGENT_API_TOKEN", token))
    print("AGENT_API_TOKEN saved to .env. Give this to your agent (shown once here):\n")
    print("  " + token + "\n")
    print("It can create drafts and read status through /api/agent/*. It cannot approve or publish. Restart the app.")
    return 0


def port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1" if host in ("0.0.0.0", "") else host, port)) == 0


def cmd_doctor(args) -> int:
    from app.config import ConfigError, Settings
    bad = warn = 0

    def line(kind, text):
        nonlocal bad, warn
        bad += kind == "FAIL"
        warn += kind == "warn"
        print(f"  {kind:<4}  {text}")

    print("IG Content Agent: checking your setup\n")
    line("ok" if sys.version_info >= (3, 11) else "FAIL", f"Python {platform.python_version()} (need 3.11 or newer)")
    for mod, need in (("flask", True), ("PIL", True), ("waitress", False)):
        try:
            __import__(mod)
            line("ok", f"{mod} installed")
        except ImportError:
            line("FAIL" if need else "warn", f"{mod} missing. Run: pip install -r requirements.txt")
    s = Settings.from_env()
    try:
        s.validate()
        line("ok", "settings are valid (secret key and password are set)")
    except ConfigError as e:
        line("FAIL", str(e))
    for tool in (s.ffmpeg_path, s.ffprobe_path):
        line("ok" if shutil.which(tool) else "FAIL", f"{tool} " + ("found" if shutil.which(tool) else "not found. Windows: winget install Gyan.FFmpeg"))
    line("ok" if s.dry_run else "warn", "DRY_RUN is on: nothing will be posted" if s.dry_run else "DRY_RUN is OFF: approved posts really go to Instagram")
    line("ok" if s.llm_provider and (s.llm_api_key or s.llm_provider == "ollama") else "warn",
         f"AI writer: {s.llm_provider}" if s.llm_provider else "No AI writer set (offline fallback is used). Set LLM_PROVIDER and LLM_API_KEY.")
    line("ok" if s.ig_configured else "warn", "Instagram account is connected" if s.ig_configured else "Instagram not connected yet (IG_USER_ID, IG_ACCESS_TOKEN)")
    line("ok" if s.public_media_base_url else "warn", "Public media address set" if s.public_media_base_url else "PUBLIC_MEDIA_BASE_URL not set (needed only for live posting)")
    if s.host == "0.0.0.0":
        line("warn", "HOST=0.0.0.0 lets other devices connect. Use https (see docs/REMOTE_ACCESS.md) and SESSION_COOKIE_SECURE=1.")
    if s.local_tts:
        from app.notify import tts_command
        line("ok" if tts_command() else "warn", "PC speech tool found" if tts_command() else "LOCAL_TTS is on but this PC has no speech tool")
    if port_in_use(s.host, s.port):
        line("warn", f"Port {s.port} is in use (the app may already be running)")
    print(f"\n{bad} problem(s), {warn} note(s).")
    return 1 if bad else 0


def cmd_run(args) -> int:
    from app import create_app
    from app.config import ConfigError, Settings
    from app.pipeline import owner_id_of
    from app.publicmedia import PublicServer
    s = Settings.from_env()
    try:
        s.validate()
    except ConfigError as e:
        print("Cannot start:", e)
        return 2
    url = f"http://localhost:{s.port}"
    if port_in_use(s.host, s.port):
        print(f"Port {s.port} is already in use. IG Content Agent is probably already running: {url}")
        if args.open:
            import webbrowser
            webbrowser.open(url)
        return 1
    app = create_app(s, start_workers=not args.no_workers)
    ctx = app.extensions["ctx"]
    pub = None
    if not port_in_use("127.0.0.1", s.public_media_port):
        pub = PublicServer(ctx.db, s)
        pub.start()
    ctx.log.info("IG Content Agent %s running at %s (dry_run=%s)", __import__("app").__version__, url, s.dry_run)
    print(f"\nIG Content Agent is running.\n  Dashboard: {url}\n  Inbox folder: {s.inbox_dir}\n  Stop with Ctrl+C\n")
    if args.open:
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    if s.tts_on_start:
        oid = owner_id_of(ctx)
        if oid:
            threading.Timer(3.0, lambda: ctx.notifier.speak_local(ctx.assistant.briefing(oid))).start()
    try:
        try:
            from waitress import serve
            serve(app, host=s.host, port=s.port, threads=8, send_bytes=1, ident="igagent", channel_timeout=300)
        except ImportError:
            from werkzeug.serving import make_server
            make_server(s.host, s.port, app, threaded=True).serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        ctx.runtime.stop()
        if pub:
            pub.stop()
    return 0


# ---- start automatically ---------------------------------------------------------------------------
def windows_task_args(python_exe: str, manage: str, open_browser: bool = True) -> list:
    tr = f'"{python_exe}" "{manage}" run' + (" --open" if open_browser else "")
    return ["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/DELAY", "0000:20", "/TN", TASK_NAME, "/TR", tr, "/RL", "LIMITED"]


def launchd_plist(python_exe: str, manage: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.igcontentagent</string>
<key>ProgramArguments</key><array><string>{python_exe}</string><string>{manage}</string><string>run</string></array>
<key>WorkingDirectory</key><string>{ROOT}</string>
<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
</dict></plist>
"""


def systemd_unit(python_exe: str, manage: str) -> str:
    return f"""[Unit]
Description=IG Content Agent
After=network-online.target

[Service]
ExecStart={python_exe} {manage} run
WorkingDirectory={ROOT}
Restart=on-failure

[Install]
WantedBy=default.target
"""


def cmd_install_autostart(args) -> int:
    py, manage = sys.executable, str(ROOT / "manage.py")
    system = platform.system()
    if system == "Windows":
        pyw = Path(py).with_name("pythonw.exe")  # no console window
        r = subprocess.run(windows_task_args(str(pyw if pyw.exists() else py), manage, not args.no_browser), capture_output=True, text=True)
        print((r.stdout or r.stderr).strip())
        if r.returncode == 0:
            print("\nIG Content Agent will start by itself each time you sign in to this PC. Logs: instance\\logs\\app.log")
        return r.returncode
    if system == "Darwin":
        p = Path.home() / "Library/LaunchAgents/com.igcontentagent.plist"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(launchd_plist(py, manage), encoding="utf-8")
        print(f"Wrote {p}\nTurn it on with: launchctl load {p}")
        return 0
    p = Path.home() / ".config/systemd/user/ig-content-agent.service"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(systemd_unit(py, manage), encoding="utf-8")
    print(f"Wrote {p}\nTurn it on with: systemctl --user enable --now ig-content-agent")
    return 0


def cmd_remove_autostart(args) -> int:
    system = platform.system()
    if system == "Windows":
        r = subprocess.run(["schtasks", "/Delete", "/F", "/TN", TASK_NAME], capture_output=True, text=True)
        print((r.stdout or r.stderr).strip())
        return r.returncode
    for p in (Path.home() / "Library/LaunchAgents/com.igcontentagent.plist", Path.home() / ".config/systemd/user/ig-content-agent.service"):
        if p.exists():
            p.unlink()
            print(f"Removed {p}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="IG Content Agent")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--username"); p.set_defaults(fn=cmd_init)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    p = sub.add_parser("run"); p.add_argument("--open", action="store_true", help="open the dashboard in your browser")
    p.add_argument("--no-workers", action="store_true"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("install-autostart"); p.add_argument("--no-browser", action="store_true"); p.set_defaults(fn=cmd_install_autostart)
    sub.add_parser("remove-autostart").set_defaults(fn=cmd_remove_autostart)
    sub.add_parser("set-password").set_defaults(fn=cmd_set_password)
    sub.add_parser("agent-token").set_defaults(fn=cmd_agent_token)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
