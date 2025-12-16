import hashlib
import logging
import os
from enum import Enum

import database


class FileStatus(Enum):
    ARRIVED = "ARRIVED"
    SENT = "SENT"


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.normpath(os.path.join(_BASE_DIR, "..", "config", "config.txt"))
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

    subject = load_template("email_subject.txt").format(filename=filename).strip()
    body = load_template("email_body.txt").format(
        filename=filename, changed=changed
    ).rstrip() + "\n"

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

        return [
            os.path.join(cdr_folder, name)
            for name in os.listdir(cdr_folder)
            if os.path.isfile(os.path.join(cdr_folder, name))
        ]
    except Exception:
        logging.exception("Failed to get files from CDR folder: %s", cdr_folder)
        return []


def calculate_hash(filepath: str) -> str | None:
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        logging.exception("Failed to calculate hash for %s", filepath)
        return None


def get_hash(file_hash: str) -> bool:
    try:
        return database.get_file_by_hash(file_hash) is not None
    except Exception:
        logging.exception("Database read error for hash %s", file_hash)
        return False


def set_hash(full_path: str, file_hash: str, status: FileStatus) -> bool:
    filename = get_filename(full_path)
    try:
        return database.insert_file(filename, file_hash, status.value)
    except Exception:
        logging.exception("Database insert error for %s (%s)", filename, file_hash)
        return False
