import datetime
import hashlib
import logging
import os
from enum import Enum

import database


class FileStatus(Enum):
    ARRIVED = "ARRIVED"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.normpath(os.path.join(_BASE_DIR, "config", "config.txt"))
TELEGRAM_ENV_PATH = os.path.join(_BASE_DIR, "secrets", "telegram.env")
RESOURCES_DIR = os.path.join(_BASE_DIR, "resources")


def load_config() -> dict[str, str]:
    config: dict[str, str] = {}

    if not os.path.isfile(CONFIG_PATH):
        raise RuntimeError("config/config.txt not found")

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
            key = key.strip()
            value = value.strip().strip("\"'")

            config[key] = value


def load_template(filename: str) -> str:
    path = os.path.join(RESOURCES_DIR, filename)
    if not os.path.isfile(path):
        raise RuntimeError(f"Template not found: {filename}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_filename(full_path: str) -> str:
    return os.path.basename(full_path)


def build_notification(full_path: str, changed: str = "") -> dict[str, str]:
    filename = get_filename(full_path)

    if not changed:
        try:
            changed = datetime.datetime.fromtimestamp(os.path.getmtime(full_path)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            logging.exception("Failed to get mtime for %s", full_path)
            changed = ""

    subject = load_template("email_subject.txt").format(filename=filename).strip()
    body = (
        load_template("email_body.txt")
        .format(filename=filename, changed=changed)
        .rstrip()
        + "\n"
    )

    return {
        "filename": filename,
        "subject": subject,
        "body": body,
        "telegram_text": body,
    }


def get_files(cdr_folder: str) -> list[str]:
    file_list: list[str] = []
    try:
        if not os.path.isdir(cdr_folder):
            raise RuntimeError(f"CDR_FOLDER does not exist: {cdr_folder}")

        for name in os.listdir(cdr_folder):
            if name.startswith("."):
                continue
            full_path = os.path.join(cdr_folder, name)
            if os.path.isfile(full_path):
                file_list.append(full_path)

        file_list.sort()
        return file_list
    except Exception:
        logging.exception("Failed to get files from CDR folder: %s", cdr_folder)
        return []


def calculate_hash(filepath: str) -> str | None:
    try:
        with open(filepath, "rb") as f:
            data = f.read()

        h = hashlib.sha256()
        h.update(filepath.encode("utf-8"))
        h.update(b"\x00")
        h.update(data)
        return h.hexdigest()
    except Exception:
        logging.exception("Failed to calculate hash for %s", filepath)
        return None


def is_known_file(full_path: str) -> bool:
    try:
        return database.get_file_by_path(full_path) is not None
    except Exception:
        logging.exception("Database read error for path %s", full_path)
        return False


def insert_file_record(full_path: str, file_hash: str, status: FileStatus, last_error: str = "") -> bool:
    filename = get_filename(full_path)
    try:
        return database.insert_file(full_path, filename, file_hash, status.value, last_error)
    except Exception:
        logging.exception("Database insert error for %s (%s)", filename, full_path)
        return False


def update_file_status(full_path: str, status: FileStatus, last_error: str = "") -> bool:
    try:
        return database.update_status(full_path, status.value, last_error)
    except Exception:
        logging.exception("Database update error for %s", full_path)
        return False


def safe_error(exc: Exception) -> str:
    msg = str(exc).strip()
    if not msg:
        msg = exc.__class__.__name__
    if len(msg) > 500:
        msg = msg[:500]
    return msg
