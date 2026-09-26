"""Ways to reach the owner: PC speakers (local text-to-speech) and Telegram on the phone."""
from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import threading
import urllib.request
from datetime import datetime


def clean_speech(text: str, limit: int = 400) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(text))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def in_quiet_hours(spec: str, now: datetime | None = None) -> bool:
    """spec like '22-7' means quiet from 22:00 to 07:00."""
    m = re.fullmatch(r"\s*(\d{1,2})\s*-\s*(\d{1,2})\s*", spec or "")
    if not m:
        return False
    a, b = int(m.group(1)), int(m.group(2))
    h = (now or datetime.now()).hour
    return (a <= h < b) if a < b else (h >= a or h < b)


def tts_command() -> list | None:
    """Command that reads text from stdin and speaks it, or None if this PC has no speech tool."""
    system = platform.system()
    if system == "Windows":
        ps = shutil.which("powershell") or shutil.which("pwsh")
        if ps:
            script = ("Add-Type -AssemblyName System.Speech; "
                      "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                      "$s.Speak([Console]::In.ReadToEnd())")
            return [ps, "-NoProfile", "-NonInteractive", "-Command", script]
    elif system == "Darwin":
        if shutil.which("say"):
            return ["say", "-f", "-"]
    else:
        for tool, args in (("espeak-ng", ["--stdin"]), ("espeak", ["--stdin"])):
            if shutil.which(tool):
                return [tool, *args]
    return None


class Notifier:
    def __init__(self, settings, runner=subprocess.run, opener=urllib.request.urlopen):
        self.s = settings
        self._run = runner
        self._open = opener
        self._speak_lock = threading.Lock()

    @property
    def local_tts_available(self) -> bool:
        return tts_command() is not None

    def speak_local(self, text: str) -> None:
        """Speak on the PC's speakers. Text goes in through stdin, never into the command line."""
        if not self.s.local_tts or in_quiet_hours(self.s.quiet_hours):
            return
        cmd = tts_command()
        text = clean_speech(text)
        if not cmd or not text:
            return

        def work():
            with self._speak_lock:
                try:
                    self._run(cmd, input=text.encode("utf-8"), timeout=60, capture_output=True)
                except Exception:
                    pass
        threading.Thread(target=work, daemon=True).start()

    def telegram(self, text: str) -> None:
        if not (self.s.telegram_bot_token and self.s.telegram_chat_id):
            return

        def work():
            try:
                body = json.dumps({"chat_id": self.s.telegram_chat_id, "text": clean_speech(text, 1000)}).encode()
                req = urllib.request.Request(f"https://api.telegram.org/bot{self.s.telegram_bot_token}/sendMessage",
                                             data=body, headers={"Content-Type": "application/json"}, method="POST")
                self._open(req, timeout=20)
            except Exception:
                pass  # never let a failed notification break the pipeline, and never log the URL (it holds the token)
        threading.Thread(target=work, daemon=True).start()

    def attention(self, text: str) -> None:
        """Something needs the owner: phone message plus a spoken alert on the PC."""
        self.telegram(text)
        self.speak_local(text)
