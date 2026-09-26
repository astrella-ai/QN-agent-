"""Uploads, validation, FFmpeg normalizing and text-to-video rendering.

Rules: file names are generated here (never taken from the client), subprocesses take argument lists
(never a shell), and every file is checked by content, not by its extension.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import shutil
import subprocess
import textwrap
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".gif"}
IMAGE_EXT = {".jpg", ".jpeg", ".png"}
ALLOWED_EXT = VIDEO_EXT | IMAGE_EXT

REEL_W, REEL_H = 1080, 1920
MIN_REEL_SECONDS, MAX_REEL_SECONDS = 3.0, 90.0  # guidance only; verify against Instagram's current docs


class MediaError(Exception):
    """A problem the owner can understand and fix. The message is safe to show."""


def sniff_kind(head: bytes) -> str | None:
    """Return 'image' or 'video' from the file's first bytes, or None if unrecognized."""
    if head[:3] == b"\xff\xd8\xff" or head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "video"  # animated GIF is converted to video
    if head[4:8] in (b"ftyp", b"moov", b"wide", b"mdat", b"free"):
        return "video"
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "video"  # webm / matroska
    return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def random_key(ext: str) -> str:
    return secrets.token_urlsafe(18).replace("-", "a").replace("_", "b") + ext.lower()


def safe_child(base: Path, key: str) -> Path:
    """Resolve a stored key to a path and make sure it stays inside base."""
    p = (base / key).resolve()
    if base.resolve() not in p.parents:
        raise MediaError("Invalid file location.")
    return p


class Ffmpeg:
    def __init__(self, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe"):
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe

    @property
    def available(self) -> bool:
        return bool(shutil.which(self.ffmpeg)) and bool(shutil.which(self.ffprobe))

    def run(self, args: list, timeout: int = 900, stdin: bytes | None = None) -> None:
        cmd = [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", *args]
        try:
            r = subprocess.run(cmd, input=stdin, capture_output=True, timeout=timeout)
        except FileNotFoundError:
            raise MediaError("FFmpeg is not installed or not on PATH. Install it and restart the app.")
        except subprocess.TimeoutExpired:
            raise MediaError("Processing took too long and was stopped.")
        if r.returncode != 0:
            tail = r.stderr.decode("utf-8", "replace").strip().splitlines()[-3:]
            raise MediaError("FFmpeg could not process this file: " + " ".join(tail)[:300])

    def probe(self, path: Path) -> dict:
        cmd = [self.ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=60)
        except FileNotFoundError:
            raise MediaError("ffprobe is not installed or not on PATH. Install FFmpeg and restart the app.")
        except subprocess.TimeoutExpired:
            raise MediaError("Reading the file took too long.")
        if r.returncode != 0:
            raise MediaError("This file is damaged or is not a real video or image.")
        try:
            data = json.loads(r.stdout.decode("utf-8", "replace"))
        except ValueError:
            raise MediaError("Could not read this file's details.")
        streams = data.get("streams", [])
        v = next((s for s in streams if s.get("codec_type") == "video"), None)
        a = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if not v:
            raise MediaError("No video or image was found in this file.")
        fmt = data.get("format", {})
        duration = 0.0
        for cand in (v.get("duration"), fmt.get("duration")):
            try:
                duration = float(cand)
                break
            except (TypeError, ValueError):
                continue
        return {"width": int(v.get("width") or 0), "height": int(v.get("height") or 0), "duration": duration,
                "codec": v.get("codec_name", ""), "pix_fmt": v.get("pix_fmt", ""), "has_audio": a is not None,
                "audio_codec": (a or {}).get("codec_name", ""), "fps": _fps(v),
                "size": int(fmt.get("size") or 0)}


def _fps(stream: dict) -> float:
    try:
        n, d = stream.get("avg_frame_rate", "0/1").split("/")
        return round(float(n) / float(d), 2) if float(d) else 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0


def spec_checks(kind: str, info: dict, media_type: str) -> list:
    """Human-readable checks. 'error' blocks approval; 'warn' explains what normalizing will fix."""
    out = []
    w, h = info["width"], info["height"]
    if w <= 0 or h <= 0:
        return [{"level": "error", "text": "The file has no readable picture size."}]
    out.append({"level": "ok", "text": f"{w}x{h} pixels"})
    if kind == "video":
        d = info["duration"]
        if d <= 0.5:
            out.append({"level": "error", "text": "The video is too short or has no length."})
        elif media_type in ("REEL", "STORY", "CAROUSEL") and d < MIN_REEL_SECONDS:
            out.append({"level": "warn", "text": f"Only {d:.1f} s long. Reels work best from {int(MIN_REEL_SECONDS)} s."})
        elif media_type == "REEL" and d > MAX_REEL_SECONDS:
            out.append({"level": "warn", "text": f"{d:.0f} s long. Check Instagram's current Reel length limit."})
        else:
            out.append({"level": "ok", "text": f"{d:.1f} seconds"})
        if info["codec"] != "h264" or info["pix_fmt"] not in ("yuv420p", "yuvj420p"):
            out.append({"level": "warn", "text": f"Codec {info['codec'] or 'unknown'}: will be converted to H.264."})
        if media_type in ("REEL", "STORY") and (w, h) != (REEL_W, REEL_H):
            out.append({"level": "warn", "text": "Not 1080x1920 (9:16): will be fitted to a vertical frame."})
        if not info["has_audio"]:
            out.append({"level": "warn", "text": "No sound track. That is fine, but many viewers expect audio."})
    else:
        ar = w / h
        if not (0.8 <= ar <= 1.91):
            out.append({"level": "warn", "text": "Shape is outside Instagram's photo range (4:5 to 1.91:1): will be padded."})
    return out


def normalize_video(ff: Ffmpeg, src: Path, dst: Path, mode: str = "blur") -> None:
    """Fit any video into 1080x1920, 30 fps, H.264 + AAC, fast-start MP4."""
    if mode == "blur":
        fc = (f"[0:v]split[a][b];[a]scale={REEL_W}:{REEL_H}:force_original_aspect_ratio=increase,"
              f"crop={REEL_W}:{REEL_H},boxblur=25:5[bg];[b]scale={REEL_W}:{REEL_H}:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=30,format=yuv420p[v]")
    elif mode == "fill":
        fc = (f"[0:v]scale={REEL_W}:{REEL_H}:force_original_aspect_ratio=increase,crop={REEL_W}:{REEL_H},"
              f"setsar=1,fps=30,format=yuv420p[v]")
    else:  # letterbox
        fc = (f"[0:v]scale={REEL_W}:{REEL_H}:force_original_aspect_ratio=decrease,"
              f"pad={REEL_W}:{REEL_H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30,format=yuv420p[v]")
    ff.run(["-i", str(src), "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-shortest", str(dst)])


def normalize_image(ff: Ffmpeg, src: Path, dst: Path, info: dict, media_type: str) -> None:
    """Convert to JPEG (what the Instagram API accepts), padding to an allowed shape."""
    w, h = info["width"], info["height"]
    if media_type == "STORY":
        tw, th = REEL_W, REEL_H
        vf = (f"scale={tw}:{th}:force_original_aspect_ratio=decrease,"
              f"pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:color=black,format=yuvj420p")
    else:
        ar = w / h
        if ar < 0.8:
            cw, ch = int(h * 0.8), h
        elif ar > 1.91:
            cw, ch = w, int(w / 1.91)
        else:
            cw, ch = w, h
        scale = min(1.0, 1440 / max(cw, ch))
        vf = (f"pad={cw}:{ch}:(ow-iw)/2:(oh-ih)/2:color=black,scale=trunc({cw}*{scale}/2)*2:trunc({ch}*{scale}/2)*2,"
              f"format=yuvj420p")
    ff.run(["-i", str(src), "-frames:v", "1", "-vf", vf, "-q:v", "2", str(dst)])


# ---- text to video --------------------------------------------------------------------------------

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/nirmalab.ttf",
    "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size: int):
    from PIL import ImageFont
    for cand in _FONT_CANDIDATES:
        if Path(cand).exists():
            try:
                return ImageFont.truetype(cand, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def _hex(c: str, default: str) -> tuple:
    c = c.lstrip("#") if re.fullmatch(r"#?[0-9a-fA-F]{6}", c or "") else default.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def script_to_lines(text: str, max_lines: int = 8, width: int = 22) -> list:
    """Split a script into short on-screen lines."""
    parts = [p.strip() for p in re.split(r"[\n]+|(?<=[.!?])\s+", text or "") if p.strip()]
    out = []
    for p in parts:
        out.append("\n".join(textwrap.wrap(p, width=width)[:6]))
        if len(out) >= max_lines:
            break
    return out


def render_text_video(ff: Ffmpeg, lines: list, dst: Path, *, bg: str, fg: str, accent: str,
                      brand: str = "", seconds_per_line: float = 2.4, fps: int = 30) -> float:
    """Draw kinetic text frames with Pillow and pipe them to FFmpeg. Returns the duration in seconds."""
    from PIL import Image, ImageDraw

    lines = [l for l in lines if l and l.strip()][:8]
    if not lines:
        raise MediaError("There is no text to turn into a video.")
    bgc, fgc, acc = _hex(bg, "#1B2430"), _hex(fg, "#F2F4F6"), _hex(accent, "#1F7A5C")
    font = _load_font(96)
    small = _load_font(44)
    frames_per = int(seconds_per_line * fps)
    fade_in, fade_out = int(0.45 * fps), int(0.30 * fps)
    cmd = [ff.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{REEL_W}x{REEL_H}", "-r", str(fps), "-i", "-", "-f", "lavfi",
           "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(dst)]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise MediaError("FFmpeg is not installed or not on PATH. Install it and restart the app.")
    try:
        base = Image.new("RGB", (REEL_W, REEL_H), bgc)
        total = len(lines)
        for idx, text in enumerate(lines):
            layer = Image.new("RGBA", (REEL_W, REEL_H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            bbox = d.multiline_textbbox((0, 0), text, font=font, align="center", spacing=18)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            d.multiline_text(((REEL_W - tw) / 2 - bbox[0], (REEL_H - th) / 2 - bbox[1]), text, font=font,
                             fill=fgc + (255,), align="center", spacing=18)
            for f in range(frames_per):
                a_in = min(1.0, f / max(1, fade_in))
                a_out = min(1.0, (frames_per - 1 - f) / max(1, fade_out))
                alpha = max(0.0, min(a_in, a_out))
                dy = int((1 - a_in) * 60)
                frame = base.copy()
                fd = ImageDraw.Draw(frame)
                prog = (idx * frames_per + f) / (total * frames_per)
                fd.rectangle([120, 1620, 120 + int((REEL_W - 240) * prog), 1628], fill=acc)
                if brand:
                    fd.text((120, 1550), brand[:40], font=small, fill=acc)
                tl = layer.copy()
                tl.putalpha(tl.getchannel("A").point(lambda v, al=alpha: int(v * al)))
                frame.paste(tl, (0, dy), tl)
                proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        err = proc.stderr.read()
        rc = proc.wait(timeout=600)
    except BrokenPipeError:
        rc, err = proc.wait(), proc.stderr.read()
    except Exception:
        proc.kill()
        raise
    if rc != 0:
        raise MediaError("FFmpeg could not build the video: " + err.decode("utf-8", "replace")[-250:])
    return total * seconds_per_line
