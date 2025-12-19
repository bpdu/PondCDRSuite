import logging
import os
import sqlite3
from typing import Optional

DB_NAME = os.environ.get("DB_NAME", "cdr_files.db").strip() or "cdr_files.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_db() -> None:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cdr_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    changed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_error TEXT
                );
                """
            )
            conn.commit()

            # Backward-compatible migration for older DBs
            try:
                cur.execute("ALTER TABLE cdr_files ADD COLUMN last_error TEXT;")
                conn.commit()
            except Exception:
                pass
    except Exception:
        logging.exception("Failed to initialize database")


def get_file_by_path(full_path: str) -> Optional[tuple]:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM cdr_files WHERE full_path = ?",
                (full_path,),
            )
            return cur.fetchone()
    except Exception:
        logging.exception("Database read error for path %s", full_path)
        return None


def insert_file(full_path: str, filename: str, file_hash: str, status: str, last_error: str = "") -> bool:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO cdr_files (full_path, filename, file_hash, status, last_error)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_path, filename, file_hash, status, last_error or None),
            )
            conn.commit()
            return True
    except Exception:
        logging.exception(
            "Failed to insert file into database: %s (%s)",
            filename,
            full_path,
        )
        return False


def update_status(full_path: str, status: str, last_error: str = "") -> bool:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE cdr_files
                SET status = ?, changed = CURRENT_TIMESTAMP, last_error = ?
                WHERE full_path = ?
                """,
                (status, last_error or None, full_path),
            )
            conn.commit()
            return True
    except Exception:
        logging.exception("Failed to update status for path %s", full_path)
        return False
