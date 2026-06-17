from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


DB_PATH = Path("database") / "email_logs.sqlite3"


SCHEMA = """
CREATE TABLE IF NOT EXISTS email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    hr_name TEXT NOT NULL,
    email TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed')),
    error_message TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(SCHEMA)
        conn.commit()


class EmailLogRepository:
    def insert_log(self, contact: dict, status: str, error_message: str = "") -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO email_logs
                (company_name, hr_name, email, timestamp, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    contact.get("company_name", ""),
                    contact.get("hr_name", "Hiring Team"),
                    contact.get("email", ""),
                    datetime.now(timezone.utc).isoformat(),
                    status,
                    error_message,
                ),
            )
            conn.commit()

    def fetch_logs(self, limit: int | None = None) -> pd.DataFrame:
        query = "SELECT id, company_name, hr_name, email, timestamp, status, error_message FROM email_logs ORDER BY id DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        with get_connection() as conn:
            return pd.read_sql_query(query, conn)

    def stats(self) -> dict[str, int]:
        with get_connection() as conn:
            rows = conn.execute("SELECT status, COUNT(*) FROM email_logs GROUP BY status").fetchall()
        return {status: count for status, count in rows}
