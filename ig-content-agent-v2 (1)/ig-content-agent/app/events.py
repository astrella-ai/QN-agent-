"""In-process event bus (for the live screen) and the persistent activity log."""
from __future__ import annotations

import queue
import threading

from .db import Database, now_iso

LEVELS = ("info", "success", "warn", "error", "attention")


class EventBus:
    def __init__(self):
        self._subs: set = set()
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=300)
        with self._lock:
            self._subs.add(q)
        return q

    def unsubscribe(self, q) -> None:
        with self._lock:
            self._subs.discard(q)

    def publish(self, owner_id: int, type_: str, data: dict) -> None:
        with self._lock:
            subs = list(self._subs)
        for q in subs:
            try:
                q.put_nowait((owner_id, type_, data))
            except queue.Full:
                pass  # a slow client loses live events; it can reload state

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subs)


class ActivityLog:
    def __init__(self, db: Database, bus: EventBus):
        self.db = db
        self.bus = bus

    def log(self, owner_id: int, message: str, level: str = "info", post_id: int | None = None,
            permission_level: str = "Observe") -> int:
        if level not in LEVELS:
            level = "info"
        message = str(message)[:500]
        ts = now_iso()
        cur = self.db.execute(
            "INSERT INTO activity(owner_id,post_id,level,permission_level,message,created_at) VALUES(?,?,?,?,?,?)",
            (owner_id, post_id, level, permission_level, message, ts))
        entry = {"id": cur.lastrowid, "post_id": post_id, "level": level,
                 "permission_level": permission_level, "message": message, "created_at": ts}
        self.bus.publish(owner_id, "activity", entry)
        return cur.lastrowid

    def since(self, owner_id: int, after_id: int, limit: int = 200) -> list:
        rows = self.db.all("SELECT * FROM activity WHERE owner_id=? AND id>? ORDER BY id ASC LIMIT ?",
                           (owner_id, after_id, limit))
        return [dict(r) for r in rows]

    def recent(self, owner_id: int, limit: int = 50) -> list:
        rows = self.db.all("SELECT * FROM activity WHERE owner_id=? ORDER BY id DESC LIMIT ?", (owner_id, limit))
        return [dict(r) for r in reversed(rows)]
