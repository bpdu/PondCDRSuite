from __future__ import annotations

import logging
import sqlite3

_conn: sqlite3.Connection | None = None


def init_db(db_path: str = "cdr_files.db") -> None:
    global _conn
    _conn = sqlite3.connect(db_path)
    try:
        with _conn:
            _conn.execute(
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
    except Exception:
        logging.exception("Failed to initialize database")


def _get_conn() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _conn


def get_file_by_filename(filename: str) -> tuple | None:
    try:
        cur = _get_conn().execute(
            "SELECT * FROM cdr_files WHERE filename = ?", (filename,)
        )
        return cur.fetchone()
    except Exception:
        logging.exception("Database read error for filename %s", filename)
        return None


def insert_file(filename: str, file_hash: str, status: str) -> bool:
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO cdr_files (filename, file_hash, status) VALUES (?, ?, ?)",
                (filename, file_hash, status),
            )
        return True
    except Exception:
        logging.exception("Failed to insert file into database: %s", filename)
        return False
