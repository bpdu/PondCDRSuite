
import logging
import os
import sqlite3
from typing import Optional

DB_NAME = os.environ.get("DB_NAME", "db.sqlite3").strip() or "db.sqlite3"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_db() -> None:
    """Initialize database"""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cdr_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL,
                    email_sent BOOLEAN DEFAULT 0,
                    telegram_sent BOOLEAN DEFAULT 0,
                    changed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()
            logging.info("Database initialized successfully")

    except sqlite3.Error as e:
        logging.exception(f"Failed to initialize database: {e}")
        raise


def get_file_by_hash(file_hash: str) -> Optional[tuple]:
    """
    Get file record by hash (filename + content).

    Args:
        file_hash: SHA256 hash of filename + content

    Returns:
        Tuple of (id, filename, file_hash, email_sent, telegram_sent, changed)
        or None if not found
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cdr_files WHERE file_hash = ?", (file_hash,))
            return cur.fetchone()
    except Exception:
        logging.exception("Database read error for hash %s", file_hash)
        return None


def insert_file(
    filename: str,
    file_hash: str,
    email_sent: bool,
    telegram_sent: bool
) -> bool:
    """
    Insert or replace file record with notification status.
    Uses file_hash as unique key - will update if same hash exists.

    Args:
        filename: Name of the CDR file
        file_hash: SHA256 hash of filename + content (unique key)
        email_sent: Whether email notification was sent
        telegram_sent: Whether telegram notification was sent

    Returns:
        True if insert/update was successful

    Raises:
        sqlite3.Error: If database operation fails
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT OR REPLACE INTO cdr_files
                   (filename, file_hash, email_sent, telegram_sent)
                   VALUES (?, ?, ?, ?)""",
                (filename, file_hash, email_sent, telegram_sent)
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logging.exception(f"Failed to insert file {filename} into database: {e}")
        return False
