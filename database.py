import sqlite3
from datetime import date

DB_PATH = "mathbot.db"

class Database:
    def __init__(self):
        self._init_db()

    def _connect(self):
        return sqlite3.connect(DB_PATH)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     INTEGER PRIMARY KEY,
                    username    TEXT,
                    is_premium  INTEGER DEFAULT 0,
                    total_queries INTEGER DEFAULT 0,
                    last_query_date TEXT,
                    daily_count INTEGER DEFAULT 0
                )
            """)

    def register_user(self, user_id: int, username: str):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )

    def is_premium(self, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT is_premium FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        return bool(row and row[0])

    def set_premium(self, user_id: int, status: bool):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET is_premium = ? WHERE user_id = ?",
                (int(status), user_id)
            )

    def get_remaining_queries(self, user_id: int, daily_limit: int) -> int:
        today = str(date.today())
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_query_date, daily_count FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
        if not row or row[0] != today:
            return daily_limit
        return max(0, daily_limit - row[1])

    def increment_usage(self, user_id: int):
        today = str(date.today())
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_query_date, daily_count FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            if row and row[0] == today:
                conn.execute(
                    "UPDATE users SET daily_count = daily_count + 1, total_queries = total_queries + 1 WHERE user_id = ?",
                    (user_id,)
                )
            else:
                conn.execute(
                    "UPDATE users SET last_query_date = ?, daily_count = 1, total_queries = total_queries + 1 WHERE user_id = ?",
                    (today, user_id)
                )

    def get_total_queries(self, user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT total_queries FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        return row[0] if row else 0
