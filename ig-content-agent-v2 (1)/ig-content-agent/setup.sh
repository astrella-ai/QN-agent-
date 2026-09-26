#!/usr/bin/env bash
# One-time setup for macOS / Linux.
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
command -v ffmpeg >/dev/null || echo "NOTE: install FFmpeg (macOS: brew install ffmpeg, Ubuntu: sudo apt install ffmpeg)"
[ -f .env ] || .venv/bin/python manage.py init
.venv/bin/python manage.py doctor || true
echo "Setup finished. Start with: ./run.sh"
