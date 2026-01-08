# utils.py

import datetime
import hashlib
import logging
import os
import time
from enum import Enum
from functools import wraps
from typing import Callable, TypeVar, Tuple

import database
from email_sender import send_email
from telegram_sender import send_telegram


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
    telegram_text = load_template("telegram_message.txt").format(filename=filename, changed=changed).rstrip()

    return {
        "filename": filename,
        "subject": subject,
        "body": body,
        "telegram_text": telegram_text,
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
    """
    Calculate SHA256 hash from filename + file content.
    This ensures same filename with different content = different hash.
    """
    try:
        filename = get_filename(filepath)
        with open(filepath, "rb") as f:
            content = f.read()
        return hashlib.sha256(filename.encode("utf-8") + content).hexdigest()
    except Exception:
        logging.exception("Failed to calculate hash for %s", filepath)
        return None


def is_known_file(full_path: str) -> bool:
    """
    Check if file (by hash) has been processed before.
    Uses hash = filename + content for lookup.
    """
    file_hash = calculate_hash(full_path)
    if not file_hash:
        return False

    try:
        return database.get_file_by_hash(file_hash) is not None
    except Exception:
        logging.exception("Database read error for file %s", get_filename(full_path))
        return False


def insert_file_record(
    full_path: str,
    file_hash: str,
    status: FileStatus,
    email_sent: bool,
    telegram_sent: bool
) -> bool:
    """
    Insert file record with notification status.

    Args:
        full_path: Full path to file
        file_hash: SHA256 hash of file
        status: Overall processing status (SENT/PARTIAL_SUCCESS/FAILED)
        email_sent: Whether email was sent successfully
        telegram_sent: Whether telegram was sent successfully

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
            telegram_sent=telegram_sent
        )
    except Exception as e:
        logging.exception("Database insert error for %s", filename)
        return False


# ============================================================================
# Business Logic Functions
# ============================================================================

def validate_config(config: dict[str, str]) -> None:
    """
    Validate required configuration fields.

    Raises:
        ConfigError: If required config is missing or invalid
    """
    # Validate CDR_FOLDER
    cdr_folder = config.get("CDR_FOLDER", "").strip()
    if not cdr_folder:
        raise ConfigError(f"CDR_FOLDER is not set in {CONFIG_PATH}")
    if not os.path.isdir(cdr_folder):
        raise ConfigError(f"CDR_FOLDER does not exist: {cdr_folder}")

    # Validate email config if enabled
    if config.get("EMAIL_SEND", "").strip().lower() == "true":
        required_email = ["SMTP_HOST", "EMAIL_FROM", "EMAIL_TO"]
        missing = [key for key in required_email if not config.get(key, "").strip()]
        if missing:
            raise ConfigError(f"Missing required email config: {', '.join(missing)}")

    # Validate telegram config if enabled
    if config.get("TELEGRAM_SEND", "").strip().lower() == "true":
        required_telegram = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
        missing = [key for key in required_telegram if not config.get(key, "").strip()]
        if missing:
            raise ConfigError(f"Missing required Telegram config: {', '.join(missing)}")

    logging.info("Configuration validated successfully")


def init_database(config: dict[str, str]) -> None:
    """
    Initialize database with optional custom DB_NAME.

    Args:
        config: Configuration dictionary
    """
    db_name = config.get("DB_NAME", "").strip()
    if db_name:
        os.environ["DB_NAME"] = db_name

    database.init_db()
    logging.info("Database initialized")


def get_new_files(config: dict[str, str]) -> list[str]:
    """
    Get list of new CDR files that haven't been processed yet.

    Args:
        config: Configuration dictionary

    Returns:
        List of full paths to new files
    """
    cdr_folder = config["CDR_FOLDER"].strip()
    all_files = get_files(cdr_folder)
    new_files = [f for f in all_files if not is_known_file(f)]

    logging.info(f"Starting CDR notify service")
    logging.info(f"Scanning folder: {cdr_folder}")
    logging.info(f"Total files: {len(all_files)}, New files: {len(new_files)}")

    return new_files


def send_notifications(file_path: str, config: dict[str, str]) -> Tuple[bool, bool, list[str]]:
    """
    Send email and Telegram notifications for a file.

    Args:
        file_path: Full path to the CDR file
        config: Configuration dictionary

    Returns:
        Tuple of (email_sent, telegram_sent, errors)
    """
    email_sent = False
    telegram_sent = False
    errors = []

    # Try email if enabled
    if config.get("EMAIL_SEND", "").strip().lower() == "true":
        try:
            email_sent = send_email(file_path, config)
        except NotificationError as e:
            errors.append(f"Email: {e}")
            logging.error(f"Email notification failed for {get_filename(file_path)}: {e}")
    else:
        email_sent = True  # Consider disabled as success

    # Try Telegram if enabled
    if config.get("TELEGRAM_SEND", "").strip().lower() == "true":
        try:
            telegram_sent = send_telegram(file_path, config)
        except NotificationError as e:
            errors.append(f"Telegram: {e}")
            logging.error(f"Telegram notification failed for {get_filename(file_path)}: {e}")
    else:
        telegram_sent = True  # Consider disabled as success

    return email_sent, telegram_sent, errors


def process_file(file_path: str, config: dict[str, str]) -> None:
    """
    Process a single CDR file: send notifications and record in database.

    This function implements the critical bug fix: files are ALWAYS saved to DB,
    even if notifications fail, to prevent infinite reprocessing.

    Args:
        file_path: Full path to the CDR file
        config: Configuration dictionary
    """
    filename = get_filename(file_path)

    # Calculate file hash
    file_hash = calculate_hash(file_path)
    if not file_hash:
        logging.error(f"Failed to calculate hash for {filename}, skipping")
        return

    # Send notifications (with retries)
    email_sent, telegram_sent, errors = send_notifications(file_path, config)

    # Determine status
    if email_sent and telegram_sent:
        status = FileStatus.SENT
    elif email_sent or telegram_sent:
        status = FileStatus.PARTIAL_SUCCESS
    else:
        status = FileStatus.FAILED

    # CRITICAL: Always save to database, regardless of notification result
    # This fixes the bug where failed notifications caused infinite reprocessing
    try:
        insert_file_record(
            full_path=file_path,
            file_hash=file_hash,
            status=status,
            email_sent=email_sent,
            telegram_sent=telegram_sent
        )

        # Log result
        if status == FileStatus.SENT:
            logging.info(f"File processed successfully: {filename}")
        elif status == FileStatus.PARTIAL_SUCCESS:
            logging.warning(
                f"Partial success for {filename}: "
                f"email={'OK' if email_sent else 'FAILED'}, "
                f"telegram={'OK' if telegram_sent else 'FAILED'}"
            )
        else:
            logging.error(f"All notifications failed for {filename}")

    except Exception as e:
        logging.error(f"Failed to save {filename} to database: {e}")
        # Note: File will be reprocessed on next run, but this is acceptable
        # since it's a database failure, not a notification failure
