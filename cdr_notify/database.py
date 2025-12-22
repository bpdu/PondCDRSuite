
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
                    filename TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    changed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()
    except Exception:
        logging.exception("Failed to initialize database")


def get_file_by_filename(filename: str) -> Optional[tuple]:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cdr_files WHERE filename = ?", (filename,))
            return cur.fetchone()
    except Exception:
        logging.exception("Database read error for filename %s", filename)
        return None


def insert_file(filename: str, file_hash: str, status: str) -> bool:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO cdr_files (filename, file_hash, status) VALUES (?, ?, ?)",
                (filename, file_hash, status),
            )
            conn.commit()
            return True
    except Exception:
        logging.exception("Failed to insert file into database: %s", filename)
        return False
