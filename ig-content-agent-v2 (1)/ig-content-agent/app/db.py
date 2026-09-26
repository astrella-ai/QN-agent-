"""SQLite access. One connection per thread, parameterized queries only."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL REFERENCES users(id),
  title TEXT NOT NULL DEFAULT '',
  brief TEXT NOT NULL DEFAULT '',
  caption TEXT NOT NULL DEFAULT '',
  hashtags TEXT NOT NULL DEFAULT '',
  media_type TEXT NOT NULL DEFAULT 'REEL',
  state TEXT NOT NULL DEFAULT 'DRAFT',
  scheduled_for TEXT,
  error TEXT NOT NULL DEFAULT '',
  remote_media_id TEXT NOT NULL DEFAULT '',
  permalink TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_posts_owner_state ON posts(owner_id, state);
CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL REFERENCES users(id),
  post_id INTEGER NOT NULL REFERENCES posts(id),
  position INTEGER NOT NULL DEFAULT 0,
  kind TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'upload',
  original_name TEXT NOT NULL DEFAULT '',
  storage_key TEXT NOT NULL,
  ready_key TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'raw',
  sha256 TEXT NOT NULL DEFAULT '',
  size_bytes INTEGER NOT NULL DEFAULT 0,
  width INTEGER NOT NULL DEFAULT 0,
  height INTEGER NOT NULL DEFAULT 0,
  duration REAL NOT NULL DEFAULT 0,
  checks_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assets_post ON assets(post_id);
CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL REFERENCES users(id),
  post_id INTEGER NOT NULL REFERENCES posts(id),
  media_sha256 TEXT NOT NULL,
  caption_sha256 TEXT NOT NULL,
  approved_at TEXT NOT NULL,
  revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS publish_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL REFERENCES users(id),
  post_id INTEGER NOT NULL REFERENCES posts(id),
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  container_id TEXT NOT NULL DEFAULT '',
  remote_media_id TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL REFERENCES users(id),
  post_id INTEGER REFERENCES posts(id),
  kind TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'queued',
  attempts INTEGER NOT NULL DEFAULT 0,
  run_at TEXT NOT NULL,
  error TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, run_at);
CREATE TABLE IF NOT EXISTS activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL,
  post_id INTEGER,
  level TEXT NOT NULL DEFAULT 'info',
  permission_level TEXT NOT NULL DEFAULT 'Observe',
  message TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pending_actions (
  token TEXT PRIMARY KEY,
  owner_id INTEGER NOT NULL,
  action_json TEXT NOT NULL,
  summary TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used_at TEXT
);
CREATE TABLE IF NOT EXISTS public_links (
  token TEXT PRIMARY KEY,
  asset_id INTEGER NOT NULL REFERENCES assets(id),
  expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kv (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class Database:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        c = self.conn()
        c.executescript(SCHEMA)

    def conn(self) -> sqlite3.Connection:
        c = getattr(self._local, "conn", None)
        if c is None:
            c = sqlite3.connect(self.path, timeout=10, isolation_level=None)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA foreign_keys=ON")
            c.execute("PRAGMA busy_timeout=8000")
            self._local.conn = c
        return c

    def execute(self, sql: str, params=()):
        return self.conn().execute(sql, params)

    def one(self, sql: str, params=()):
        return self.conn().execute(sql, params).fetchone()

    def all(self, sql: str, params=()):
        return self.conn().execute(sql, params).fetchall()

    @contextmanager
    def tx(self):
        c = self.conn()
        c.execute("BEGIN IMMEDIATE")
        try:
            yield c
        except BaseException:
            c.execute("ROLLBACK")
            raise
        else:
            c.execute("COMMIT")

    def kv_get(self, key: str, default: str = "") -> str:
        row = self.one("SELECT value FROM kv WHERE key=?", (key,))
        return row["value"] if row else default

    def kv_set(self, key: str, value: str) -> None:
        self.execute("INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                     (key, value))
