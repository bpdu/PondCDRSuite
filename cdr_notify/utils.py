from __future__ import annotations

import datetime
import hashlib
import logging
import os
from enum import Enum

from . import database


class FileStatus(Enum):
    SENT = "SENT"


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.normpath(os.path.join(_BASE_DIR, "config", "config.txt"))
TELEGRAM_ENV_PATH = os.path.join(_BASE_DIR, ".env", "telegram.env")
SMTP_ENV_PATH = os.path.join(_BASE_DIR, ".env", "smtp.env")
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

    if os.path.isfile(SMTP_ENV_PATH):
        _load_env_file(SMTP_ENV_PATH, config)

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
        changed = datetime.datetime.fromtimestamp(
            os.path.getmtime(full_path)
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        logging.exception("Failed to get mtime for %s", full_path)

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
    if not os.path.isdir(cdr_folder):
        raise RuntimeError(f"CDR_FOLDER does not exist: {cdr_folder}")

    files: list[str] = []
    for name in sorted(os.listdir(cdr_folder)):
        if name.startswith("."):
            continue

        full_path = os.path.join(cdr_folder, name)
        if os.path.isfile(full_path):
            files.append(full_path)

    return files


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
    return database.get_file_by_filename(filename) is not None


def insert_file_record(full_path: str, file_hash: str, status: FileStatus) -> bool:
    filename = get_filename(full_path)
    return database.insert_file(filename, file_hash, status.value)
