
import logging
import os
import sqlite3
from typing import Optional

DB_NAME = os.environ.get("DB_NAME", "db.sqlite3").strip() or "db.sqlite3"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_db() -> None:
    """Initialize database with schema migration support"""
    try:
        with get_connection() as conn:
            cur = conn.cursor()

            # Create table with new schema
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cdr_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    email_sent BOOLEAN DEFAULT 0,
                    telegram_sent BOOLEAN DEFAULT 0,
                    changed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Migrate existing databases - add new columns if they don't exist
            cur.execute("PRAGMA table_info(cdr_files)")
            existing_columns = {row[1] for row in cur.fetchall()}

            if 'email_sent' not in existing_columns:
                cur.execute("ALTER TABLE cdr_files ADD COLUMN email_sent BOOLEAN DEFAULT 0")
                logging.info("Database migration: Added email_sent column")

            if 'telegram_sent' not in existing_columns:
                cur.execute("ALTER TABLE cdr_files ADD COLUMN telegram_sent BOOLEAN DEFAULT 0")
                logging.info("Database migration: Added telegram_sent column")

            conn.commit()
            logging.info("Database initialized successfully")

    except sqlite3.Error as e:
        logging.exception(f"Failed to initialize database: {e}")
        raise


def get_file_by_filename(filename: str) -> Optional[tuple]:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cdr_files WHERE filename = ?", (filename,))
            return cur.fetchone()
    except Exception:
        logging.exception("Database read error for filename %s", filename)
        return None


def insert_file(
    filename: str,
    file_hash: str,
    status: str,
    email_sent: bool,
    telegram_sent: bool
) -> bool:
    """
    Insert file record with notification status.

    Args:
        filename: Name of the CDR file
        file_hash: SHA256 hash of the file
        status: Overall status (SENT/PARTIAL/FAILED)
        email_sent: Whether email notification was sent
        telegram_sent: Whether telegram notification was sent

    Returns:
        True if insert was successful

    Raises:
        sqlite3.Error: If database insert fails
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO cdr_files
                   (filename, file_hash, status, email_sent, telegram_sent)
                   VALUES (?, ?, ?, ?, ?)""",
                (filename, file_hash, status, email_sent, telegram_sent)
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logging.exception(f"Failed to insert file {filename} into database: {e}")
        return False
