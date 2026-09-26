"""Settings from environment and .env. The app fails closed on missing secrets."""
from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ConfigError(RuntimeError):
    pass


def parse_dotenv(text: str) -> dict:
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key.strip()] = value
    return out


def load_env(path: Path | None = None) -> dict:
    values: dict = {}
    p = path or (ROOT / ".env")
    if p.exists():
        values.update(parse_dotenv(p.read_text(encoding="utf-8")))
    values.update(os.environ)  # real environment wins over the file
    return values


def _bool(v, default=False) -> bool:
    if v is None or v == "":
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def _int(v, default: int) -> int:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


def _list(v) -> tuple:
    return tuple(x.strip() for x in str(v or "").split(",") if x.strip())


@dataclass(frozen=True)
class Settings:
    env: str = "production"
    debug: bool = False
    secret_key: str = ""
    admin_username: str = "owner"
    admin_password_hash: str = ""
    host: str = "127.0.0.1"
    port: int = 5057
    public_media_port: int = 5058
    public_media_base_url: str = ""
    allowed_hosts: tuple = ()
    allowed_origins: tuple = ()
    cookie_secure: bool = False
    data_dir: Path = ROOT / "instance"
    max_upload_mb: int = 200
    dry_run: bool = True
    workers: bool = True
    llm_provider: str = ""
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    ig_user_id: str = ""
    ig_access_token: str = ""
    graph_version: str = "v22.0"
    agent_api_token: str = ""
    local_tts: bool = False
    tts_on_start: bool = False
    quiet_hours: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    brand_name: str = ""
    brand_bg: str = "#1B2430"
    brand_fg: str = "#F2F4F6"
    brand_accent: str = "#1F7A5C"
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"

    @property
    def inbox_dir(self) -> Path:
        return self.data_dir / "inbox"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def ig_configured(self) -> bool:
        return bool(self.ig_user_id and self.ig_access_token)

    @classmethod
    def from_env(cls, env: dict | None = None) -> "Settings":
        e = env if env is not None else load_env()
        g = e.get
        data_dir = Path(g("DATA_DIR") or (ROOT / "instance"))
        return cls(
            env=(g("APP_ENV") or "production").lower(),
            debug=_bool(g("FLASK_DEBUG"), False),
            secret_key=g("SECRET_KEY", ""),
            admin_username=g("ADMIN_USERNAME") or "owner",
            admin_password_hash=g("ADMIN_PASSWORD_HASH", ""),
            host=g("HOST") or "127.0.0.1",
            port=_int(g("PORT"), 5057),
            public_media_port=_int(g("PUBLIC_MEDIA_PORT"), 5058),
            public_media_base_url=(g("PUBLIC_MEDIA_BASE_URL") or "").rstrip("/"),
            allowed_hosts=_list(g("ALLOWED_HOSTS")),
            allowed_origins=_list(g("ALLOWED_ORIGINS")),
            cookie_secure=_bool(g("SESSION_COOKIE_SECURE"), False),
            data_dir=data_dir,
            max_upload_mb=_int(g("MAX_UPLOAD_MB"), 200),
            dry_run=_bool(g("DRY_RUN"), True),
            workers=_bool(g("WORKERS"), True),
            llm_provider=(g("LLM_PROVIDER") or "").lower(),
            llm_model=g("LLM_MODEL", ""),
            llm_api_key=g("LLM_API_KEY", ""),
            llm_base_url=(g("LLM_BASE_URL") or "").rstrip("/"),
            ig_user_id=g("IG_USER_ID", ""),
            ig_access_token=g("IG_ACCESS_TOKEN", ""),
            graph_version=g("GRAPH_API_VERSION") or "v22.0",
            agent_api_token=g("AGENT_API_TOKEN", ""),
            local_tts=_bool(g("LOCAL_TTS"), False),
            tts_on_start=_bool(g("TTS_ON_START"), False),
            quiet_hours=g("QUIET_HOURS", ""),
            telegram_bot_token=g("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=g("TELEGRAM_CHAT_ID", ""),
            brand_name=g("BRAND_NAME", ""),
            brand_bg=g("BRAND_BG") or "#1B2430",
            brand_fg=g("BRAND_FG") or "#F2F4F6",
            brand_accent=g("BRAND_ACCENT") or "#1F7A5C",
            ffmpeg_path=g("FFMPEG_PATH") or "ffmpeg",
            ffprobe_path=g("FFPROBE_PATH") or "ffprobe",
        )

    def validate(self) -> None:
        """Refuse to start with unsafe or missing configuration."""
        problems = []
        if len(self.secret_key) < 32:
            problems.append("SECRET_KEY is missing or shorter than 32 characters (run: python manage.py init)")
        if not self.admin_password_hash:
            problems.append("ADMIN_PASSWORD_HASH is missing (run: python manage.py init)")
        if self.env == "production" and self.debug:
            problems.append("FLASK_DEBUG must be 0 in production")
        if "*" in self.allowed_origins:
            problems.append("ALLOWED_ORIGINS must not contain '*'")
        if self.public_media_base_url and not self.public_media_base_url.startswith("https://"):
            problems.append("PUBLIC_MEDIA_BASE_URL must start with https:// (Instagram fetches media over HTTPS)")
        if problems:
            raise ConfigError("; ".join(problems))

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.media_dir, self.inbox_dir, self.logs_dir,
                  self.inbox_dir / "processed", self.inbox_dir / "rejected", self.media_dir / "tmp"):
            d.mkdir(parents=True, exist_ok=True)


def settings_field_names() -> list:
    return [f.name for f in fields(Settings)]
