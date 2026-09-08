"""
SQLite persistence layer.

Why SQLite instead of the original raw JSON files:
- Atomic writes (no half-written files if the process is killed mid-save)
- No "read whole file into RAM, mutate, write whole file back" on every action
- Safe under concurrent handlers (WAL mode)
- Trivial to back up: it's one file
"""
import sqlite3
import threading
import time
from contextlib import contextmanager

import config

_lock = threading.Lock()
_conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
_conn.execute("PRAGMA journal_mode=WAL;")
_conn.row_factory = sqlite3.Row


@contextmanager
def _cursor():
    with _lock:
        cur = _conn.cursor()
        try:
            yield cur
            _conn.commit()
        finally:
            cur.close()


def init_db():
    with _cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_seen INTEGER
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS banned (
            user_id INTEGER PRIMARY KEY,
            banned_at INTEGER
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_at INTEGER
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS force_sub_channels (
            channel_id INTEGER PRIMARY KEY,
            title TEXT,
            invite_link TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            channel_msg_id INTEGER,
            uploader_id INTEGER,
            file_type TEXT,
            uploaded_at INTEGER
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")
        # Seed owner as permanent admin
        cur.execute(
            "INSERT OR IGNORE INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (config.OWNER_ID, config.OWNER_ID, int(time.time())),
        )
        # Seed default settings if not present
        defaults = {
            "welcome_msg": config.DEFAULT_WELCOME_MSG,
            "auto_delete_seconds": str(config.DEFAULT_AUTO_DELETE_SECONDS),
            "protect_content": config.DEFAULT_PROTECT_CONTENT,
            "storage_channel_id": "",
        }
        for k, v in defaults.items():
            cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))


# ---------------- Users ----------------

def track_user(user_id: int):
    with _cursor() as cur:
        cur.execute(
            "INSERT OR IGNORE INTO users (user_id, first_seen) VALUES (?, ?)",
            (user_id, int(time.time())),
        )


def user_count() -> int:
    with _cursor() as cur:
        return cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def all_user_ids() -> list:
    with _cursor() as cur:
        return [r[0] for r in cur.execute("SELECT user_id FROM users").fetchall()]


# ---------------- Bans ----------------

def is_banned(user_id: int) -> bool:
    with _cursor() as cur:
        return cur.execute("SELECT 1 FROM banned WHERE user_id=?", (user_id,)).fetchone() is not None


def ban_user(user_id: int):
    with _cursor() as cur:
        cur.execute("INSERT OR REPLACE INTO banned (user_id, banned_at) VALUES (?, ?)", (user_id, int(time.time())))


def unban_user(user_id: int):
    with _cursor() as cur:
        cur.execute("DELETE FROM banned WHERE user_id=?", (user_id,))


def banned_count() -> int:
    with _cursor() as cur:
        return cur.execute("SELECT COUNT(*) FROM banned").fetchone()[0]


# ---------------- Admins ----------------

def is_admin(user_id: int) -> bool:
    if user_id == config.OWNER_ID:
        return True
    with _cursor() as cur:
        return cur.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,)).fetchone() is not None


def is_owner(user_id: int) -> bool:
    return user_id == config.OWNER_ID


def add_admin(user_id: int, added_by: int):
    with _cursor() as cur:
        cur.execute(
            "INSERT OR IGNORE INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (user_id, added_by, int(time.time())),
        )


def remove_admin(user_id: int) -> bool:
    if user_id == config.OWNER_ID:
        return False  # owner can never be removed
    with _cursor() as cur:
        cur.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
    return True


def list_admins() -> list:
    with _cursor() as cur:
        return [r[0] for r in cur.execute("SELECT user_id FROM admins ORDER BY added_at").fetchall()]


# ---------------- Force-Sub Channels ----------------

def add_force_sub_channel(channel_id: int, title: str, invite_link: str):
    with _cursor() as cur:
        cur.execute(
            "INSERT OR REPLACE INTO force_sub_channels (channel_id, title, invite_link) VALUES (?, ?, ?)",
            (channel_id, title, invite_link),
        )


def remove_force_sub_channel(channel_id: int):
    with _cursor() as cur:
        cur.execute("DELETE FROM force_sub_channels WHERE channel_id=?", (channel_id,))


def list_force_sub_channels() -> list:
    with _cursor() as cur:
        return cur.execute("SELECT channel_id, title, invite_link FROM force_sub_channels").fetchall()


# ---------------- Files ----------------

def add_file(file_id: str, channel_msg_id: int, uploader_id: int, file_type: str):
    with _cursor() as cur:
        cur.execute(
            "INSERT OR REPLACE INTO files (file_id, channel_msg_id, uploader_id, file_type, uploaded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (file_id, channel_msg_id, uploader_id, file_type, int(time.time())),
        )


def get_file(file_id: str):
    with _cursor() as cur:
        return cur.execute(
            "SELECT file_id, channel_msg_id, uploader_id, file_type, uploaded_at FROM files WHERE file_id=?",
            (file_id,),
        ).fetchone()


def delete_file(file_id: str) -> bool:
    with _cursor() as cur:
        cur.execute("DELETE FROM files WHERE file_id=?", (file_id,))
        return cur.rowcount > 0


def clear_files():
    with _cursor() as cur:
        cur.execute("DELETE FROM files")


def file_count() -> int:
    with _cursor() as cur:
        return cur.execute("SELECT COUNT(*) FROM files").fetchone()[0]


def recent_files(limit: int = 10) -> list:
    with _cursor() as cur:
        return cur.execute(
            "SELECT file_id, file_type, uploaded_at FROM files ORDER BY uploaded_at DESC LIMIT ?",
            (limit,),
        ).fetchall()


# ---------------- Settings (key/value store) ----------------

def get_setting(key: str, default: str = "") -> str:
    with _cursor() as cur:
        row = cur.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default


def set_setting(key: str, value: str):
    with _cursor() as cur:
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
