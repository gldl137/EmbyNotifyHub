"""
SQLite 数据库统一数据层

取代原有 JSON 文件存储：
  - data/config.json              -> config 表
  - data/events.json             -> events 表
  - data/notifications/*.json    -> notifications 表

对外暴露单例 DB，并提供 migrate_json_to_sqlite() 将既有 JSON 数据迁移进库。
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _resolve_data_dir() -> Path:
    if os.getenv("DATA_DIR"):
        return Path(os.getenv("DATA_DIR"))
    return Path(__file__).parent.parent.parent.parent / "data"


class Database:
    """轻量 SQLite 封装（使用标准库 sqlite3）"""

    def __init__(self, db_path: Optional[Path] = None):
        self.data_dir = _resolve_data_dir()
        self.db_path = db_path or (self.data_dir / "database.sqlite")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self._init_schema()

    @property
    def conn(self):
        if self._conn is None:
            import sqlite3
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id        TEXT PRIMARY KEY,
                data      TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id        TEXT PRIMARY KEY,
                event_id  TEXT NOT NULL,
                type      TEXT NOT NULL,
                ts        TEXT NOT NULL,
                meta      TEXT NOT NULL,
                data      TEXT NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_event_id ON notifications(event_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)")
        self.conn.commit()

    # ---------- config ----------
    def get_config(self, key: str, default: Any = None) -> Any:
        row = self.conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def set_config(self, key: str, value: Any):
        self.conn.execute(
            "INSERT INTO config(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value, ensure_ascii=False)),
        )
        self.conn.commit()

    def update_config(self, mapping: Dict[str, Any]):
        for k, v in mapping.items():
            self.set_config(k, v)

    def get_all_config(self) -> Dict[str, Any]:
        rows = self.conn.execute("SELECT key, value FROM config").fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    # ---------- events ----------
    def add_event(self, event_id: str, data: Dict[str, Any], created_at: str):
        self.conn.execute(
            "INSERT INTO events(id, data, created_at) VALUES(?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET data=excluded.data, created_at=excluded.created_at",
            (event_id, json.dumps(data, ensure_ascii=False), created_at),
        )
        self.conn.commit()

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute("SELECT data FROM events WHERE id=?", (event_id,)).fetchone()
        return json.loads(row["data"]) if row else None

    def get_all_events(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT data FROM events ORDER BY created_at DESC").fetchall()
        return [json.loads(r["data"]) for r in rows]

    def delete_event(self, event_id: str):
        self.conn.execute("DELETE FROM events WHERE id=?", (event_id,))
        self.conn.commit()

    def clear_events(self):
        self.conn.execute("DELETE FROM events")
        self.conn.commit()

    def trim_events(self, max_count: int):
        """仅保留最近 max_count 条事件（按 created_at 倒序），用于循环覆盖"""
        rows = self.conn.execute(
            "SELECT id FROM events ORDER BY created_at DESC LIMIT -1 OFFSET ?", (max_count,)
        ).fetchall()
        ids = [r["id"] for r in rows]
        if ids:
            placeholders = ",".join("?" * len(ids))
            self.conn.execute(f"DELETE FROM events WHERE id IN ({placeholders})", ids)
            self.conn.commit()

    # ---------- notifications ----------
    def add_notification(self, record_id: str, event_id: str, ntype: str,
                          ts: str, meta: Dict[str, Any], data: Dict[str, Any]):
        self.conn.execute(
            "INSERT INTO notifications(id, event_id, type, ts, meta, data) VALUES(?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET event_id=excluded.event_id, type=excluded.type, "
            "ts=excluded.ts, meta=excluded.meta, data=excluded.data",
            (record_id, event_id, ntype, ts,
             json.dumps(meta, ensure_ascii=False), json.dumps(data, ensure_ascii=False)),
        )
        self.conn.commit()

    def get_notifications_by_type(self, ntype: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, event_id, type, ts, meta, data FROM notifications WHERE type=? ORDER BY ts DESC",
            (ntype,),
        ).fetchall()
        return [self._row_to_notification(r) for r in rows]

    def get_notification_by_event_id(self, event_id: str,
                                     ntype: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if ntype:
            row = self.conn.execute(
                "SELECT id, event_id, type, ts, meta, data FROM notifications "
                "WHERE event_id=? AND type=? ORDER BY ts DESC LIMIT 1",
                (event_id, ntype),
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT id, event_id, type, ts, meta, data FROM notifications "
                "WHERE event_id=? ORDER BY ts DESC LIMIT 1",
                (event_id,),
            ).fetchone()
        return self._row_to_notification(row) if row else None

    def get_all_notifications_by_event_id(self, event_id: str) -> Dict[str, Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, event_id, type, ts, meta, data FROM notifications WHERE event_id=?",
            (event_id,),
        ).fetchall()
        result: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            rec = self._row_to_notification(r)
            result[rec["type"]] = rec
        return result

    def delete_notifications_by_event_id(self, event_id: str):
        self.conn.execute("DELETE FROM notifications WHERE event_id=?", (event_id,))
        self.conn.commit()

    def clear_notifications(self):
        self.conn.execute("DELETE FROM notifications")
        self.conn.commit()

    @staticmethod
    def _row_to_notification(row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "event_id": row["event_id"],
            "type": row["type"],
            "timestamp": row["ts"],
            "data": json.loads(row["data"]),
            **json.loads(row["meta"]),
        }


# 全局单例
_db: Optional[Database] = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def migrate_json_to_sqlite():
    """
    将既有 JSON 文件数据迁移进 SQLite（幂等，可重复运行）。
    迁移完成后原 JSON 文件保留但不再被读写。
    """
    import json as _json
    from pathlib import Path as _Path

    db = get_db()
    data_dir = db.data_dir

    # ---- events.json ----
    events_path = data_dir / "events.json"
    if events_path.exists():
        try:
            events = _json.loads(events_path.read_text(encoding="utf-8"))
            if isinstance(events, list):
                for ev in events:
                    eid = ev.get("core", {}).get("id")
                    ts = ev.get("core", {}).get("timestamp", "")
                    if eid:
                        db.add_event(eid, ev, ts)
                logger.info(f"已迁移 events.json ({len(events)} 条)")
        except Exception as e:
            logger.error(f"迁移 events.json 失败: {e}")

    # ---- notifications/*.json ----
    notif_dir = data_dir / "notifications"
    if notif_dir.exists():
        type_map = {
            "desktop.json": "desktop",
            "wecom.json": "wecom",
        }
        for fname, ntype in type_map.items():
            fpath = notif_dir / fname
            if fpath.exists():
                try:
                    records = _json.loads(fpath.read_text(encoding="utf-8"))
                    if isinstance(records, list):
                        for rec in records:
                            rid = rec.get("id")
                            eid = rec.get("event_id")
                            ts = rec.get("timestamp", "")
                            data = rec.get("data", {})
                            meta = {k: v for k, v in rec.items()
                                    if k not in ("id", "event_id", "type", "timestamp", "data")}
                            if rid:
                                db.add_notification(rid, eid, ntype, ts, meta, data)
                        logger.info(f"已迁移 {fname} ({len(records)} 条)")
                except Exception as e:
                    logger.error(f"迁移 {fname} 失败: {e}")
