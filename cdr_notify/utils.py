# utils.py

import datetime
import hashlib
import logging
import os
import time
from enum import Enum
from functools import wraps
from typing import Callable, TypeVar

import database


# Custom Exceptions
class CDRNotifyError(Exception):
    """Base exception for CDR notify application"""
    pass


class ConfigError(CDRNotifyError):
    """Configuration validation errors"""
    pass


class NotificationError(CDRNotifyError):
    """Notification sending failures"""
    pass


class DatabaseError(CDRNotifyError):
    """Database operation failures"""
    pass


class FileStatus(Enum):
    SENT = "SENT"
    PARTIAL_SUCCESS = "PARTIAL"
    FAILED = "FAILED"


T = TypeVar('T')


def retry(max_attempts: int = 3, backoff_base: float = 2.0):
    """
    Simple retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        backoff_base: Base for exponential backoff in seconds (default: 2.0)
                     Delays will be: 2s, 4s, 8s
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except NotificationError as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = backoff_base ** attempt
                        logging.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logging.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.normpath(os.path.join(_BASE_DIR, "config", "config.txt"))
TELEGRAM_ENV_PATH = os.path.join(_BASE_DIR, "secrets", "telegram.env")
RESOURCES_DIR = os.path.join(_BASE_DIR, "resources")


def is_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> dict[str, str]:
    config: dict[str, str] = {}

    if not os.path.isfile(CONFIG_PATH):
        raise RuntimeError(f"Config file not found: {CONFIG_PATH}")

    _load_env_file(CONFIG_PATH, config)

    if os.path.isfile(TELEGRAM_ENV_PATH):
        _load_env_file(TELEGRAM_ENV_PATH, config)

    return config


def _load_env_file(path: str, config: dict[str, str]) -> None:
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            config[key.strip()] = value.strip().strip("\"'")


def load_template(filename: str) -> str:
    path = os.path.join(RESOURCES_DIR, filename)
    if not os.path.isfile(path):
        raise RuntimeError(f"Template not found: {filename}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_filename(full_path: str) -> str:
    return os.path.basename(full_path)


def build_notification(full_path: str) -> dict[str, str]:
    filename = get_filename(full_path)

    changed = ""
    try:
        changed = datetime.datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        logging.exception("Failed to get mtime for %s", full_path)

    subject = load_template("email_subject.txt").format(filename=filename).strip()
    body = load_template("email_body.txt").format(filename=filename, changed=changed).rstrip() + "\n"

    return {
        "filename": filename,
        "subject": subject,
        "body": body,
        "telegram_text": body,
    }


def get_files(cdr_folder: str) -> list[str]:
    try:
        if not os.path.isdir(cdr_folder):
            raise RuntimeError(f"CDR_FOLDER does not exist: {cdr_folder}")

        files: list[str] = []
        for name in os.listdir(cdr_folder):
            if name.startswith("."):
                continue

            full_path = os.path.join(cdr_folder, name)
            if os.path.isfile(full_path):
                files.append(full_path)

        files.sort()
        return files

    except Exception:
        logging.exception("Failed to list files in %s", cdr_folder)
        return []


def calculate_hash(filepath: str) -> str | None:
    try:
        with open(filepath, "rb") as f:
            content = f.read()
        return hashlib.sha256(filepath.encode("utf-8") + content).hexdigest()
    except Exception:
        logging.exception("Failed to calculate hash for %s", filepath)
        return None


def is_known_file(full_path: str) -> bool:
    filename = get_filename(full_path)
    try:
        return database.get_file_by_filename(filename) is not None
    except Exception:
        logging.exception("Database read error for filename %s", filename)
        return False


def insert_file_record(
    full_path: str,
    file_hash: str,
    status: FileStatus,
    email_sent: bool,
    telegram_sent: bool,
    error_message: str | None = None,
    retry_count: int = 0
) -> bool:
    """
    Insert file record with detailed status.

    Args:
        full_path: Full path to file
        file_hash: SHA256 hash of file
        status: Overall processing status (SENT/PARTIAL_SUCCESS/FAILED)
        email_sent: Whether email was sent successfully
        telegram_sent: Whether telegram was sent successfully
        error_message: Optional error details
        retry_count: Number of retry attempts made

    Returns:
        True if insert was successful, False otherwise
    """
    filename = get_filename(full_path)
    try:
        return database.insert_file(
            filename=filename,
            file_hash=file_hash,
            status=status.value,
            email_sent=email_sent,
            telegram_sent=telegram_sent,
            error_message=error_message,
            retry_count=retry_count
        )
    except Exception as e:
        logging.exception("Database insert error for %s", filename)
        return False
