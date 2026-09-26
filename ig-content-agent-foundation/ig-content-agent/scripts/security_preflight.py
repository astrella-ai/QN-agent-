#!/usr/bin/env python3
"""Security pre-flight. Run before every commit and every deploy.

Checks:
  1. .env files are git-ignored and not tracked
  2. No secret-looking values in the working tree
  3. No .env files or secret-looking values anywhere in git history
  4. Debug mode is not enabled in code or example config

Exit code 0 = all checks passed, 1 = at least one failed.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "venv", ".venv", "node_modules", "__pycache__", "instance"}
SKIP_FILES = {"security_preflight.py"}
ENV_FILE = re.compile(r"(^|/)\.env(\..+)?$")
ENV_ALLOWED = {".env.example"}

SECRET_PATTERNS = {
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Meta/Facebook access token": re.compile(r"EAA[A-Za-z0-9]{40,}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "OpenAI-style key": re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    "Private key block": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "Hardcoded secret assignment": re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-/+=]{20,}"
    ),
}

failures = []


def fail(msg):
    failures.append(msg)
    print(f"  FAIL  {msg}")


def ok(msg):
    print(f"  ok    {msg}")


def git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, errors="replace")
    except FileNotFoundError:
        return None
    return r if r.returncode == 0 else None


def is_repo():
    return git("rev-parse", "--is-inside-work-tree") is not None


def check_gitignore():
    print("[1] .env handling")
    gi = ROOT / ".gitignore"
    text = gi.read_text() if gi.exists() else ""
    if re.search(r"(?m)^\.env\s*$", text) and re.search(r"(?m)^\.env\.\*\s*$", text):
        ok(".gitignore ignores .env and .env.*")
    else:
        fail(".gitignore must contain '.env' and '.env.*' lines")
    if is_repo():
        tracked = git("ls-files")
        bad = [f for f in (tracked.stdout.splitlines() if tracked else [])
               if ENV_FILE.search(f) and Path(f).name not in ENV_ALLOWED]
        if bad:
            fail(f"tracked env files: {', '.join(bad)}")
        else:
            ok("no .env files tracked by git")
    else:
        print("  skip  not a git repository yet (run 'git init' first)")


def scan_text(label, text):
    hits = []
    for name, pat in SECRET_PATTERNS.items():
        if pat.search(text):
            hits.append(name)
    return hits


def check_tree():
    print("[2] Working tree secrets")
    found = False
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SKIP_FILES or ENV_FILE.search(fn) and fn not in ENV_ALLOWED:
                continue  # real .env files hold secrets by design; they must be ignored (check 1)
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size > 1_000_000:
                    continue
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            for hit in scan_text(str(p), text):
                found = True
                fail(f"{p.relative_to(ROOT)}: looks like {hit}")
    if not found:
        ok("no secret-looking values found")


def check_history():
    print("[3] Git history")
    if not is_repo():
        print("  skip  not a git repository yet")
        return
    if git("rev-parse", "HEAD") is None:
        print("  skip  no commits yet")
        return
    names = git("log", "--all", "--name-only", "--pretty=format:")
    bad = sorted({f for f in (names.stdout.splitlines() if names else [])
                  if f and ENV_FILE.search(f) and Path(f).name not in ENV_ALLOWED})
    if bad:
        fail(f"env files exist in history: {', '.join(bad)} (rotate those secrets, then purge history)")
    else:
        ok("no .env files ever committed")
    patch = git("log", "--all", "-p", "--no-color")
    hits = scan_text("history", patch.stdout[:50_000_000]) if patch else []
    if hits:
        fail(f"secret-looking values in history: {', '.join(hits)}")
    else:
        ok("no secret-looking values in history")


def check_debug():
    print("[4] Debug mode")
    bad = False
    for p in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts) or not p.is_file() or p.name in SKIP_FILES:
            continue
        if p.suffix == ".py" or p.name.startswith(".env"):
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            if re.search(r"debug\s*=\s*True", text) or re.search(r"(?m)^FLASK_DEBUG\s*=\s*(1|true)\s*$", text, re.I):
                bad = True
                fail(f"{p.relative_to(ROOT)}: debug mode enabled")
    if not bad:
        ok("debug mode not enabled")


def main():
    print("Security pre-flight\n")
    check_gitignore()
    check_tree()
    check_history()
    check_debug()
    print()
    if failures:
        print(f"{len(failures)} check(s) failed. Fix them before committing or deploying.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
