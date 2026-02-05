from __future__ import annotations

import datetime
import hashlib
import logging
import os
from enum import Enum

import database


class FileStatus(Enum):
    SENT = "SENT"


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.normpath(os.path.join(_BASE_DIR, "config", "config.txt"))
TELEGRAM_ENV_PATH = os.path.join(_BASE_DIR, ".env", "telegram.env")
MSGRAPH_ENV_PATH = os.path.join(_BASE_DIR, ".env", "msgraph.env")
RESOURCES_DIR = os.path.join(_BASE_DIR, "resources")
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB


def is_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> dict[str, str]:
    config: dict[str, str] = {}

    if not os.path.isfile(CONFIG_PATH):
        raise RuntimeError(f"Config file not found: {CONFIG_PATH}")

    _load_env_file(CONFIG_PATH, config)

    if os.path.isfile(TELEGRAM_ENV_PATH):
        _load_env_file(TELEGRAM_ENV_PATH, config)

    if os.path.isfile(MSGRAPH_ENV_PATH):
        _load_env_file(MSGRAPH_ENV_PATH, config)

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

    replacements = {"{filename}": filename, "{changed}": changed}

    subject = load_template("email_subject.txt")
    body = load_template("email_body.txt")
    telegram_text = load_template("telegram_body.txt")

    for key, value in replacements.items():
        subject = subject.replace(key, value)
        body = body.replace(key, value)
        telegram_text = telegram_text.replace(key, value)

    subject = subject.strip()
    body = body.rstrip() + "\n"
    telegram_text = telegram_text.rstrip() + "\n"

    return {
        "filename": filename,
        "subject": subject,
        "body": body,
        "telegram_text": telegram_text,
    }


def get_files(cdr_folder: str) -> list[str]:
    if not os.path.isdir(cdr_folder):
        raise RuntimeError(f"CDR_FOLDER does not exist: {cdr_folder}")

    files: list[str] = []
    for name in sorted(os.listdir(cdr_folder)):
        if name.startswith("."):
            continue

        full_path = os.path.join(cdr_folder, name)
        try:
            if not os.path.isfile(full_path) or os.path.islink(full_path):
                continue
        except OSError:
            continue

        files.append(full_path)

    return files


def calculate_hash(filepath: str) -> str | None:
    try:
        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE:
            logging.warning("File too large (%d bytes), skipping: %s", file_size, filepath)
            return None
        with open(filepath, "rb") as f:
            content = f.read()
        return hashlib.sha256(filepath.encode("utf-8") + content).hexdigest()
    except Exception:
        logging.exception("Failed to calculate hash for %s", filepath)
        return None


def is_known_hash(file_hash: str) -> bool:
    return database.get_file_by_hash(file_hash) is not None


def insert_file_record(full_path: str, file_hash: str, status: FileStatus) -> bool:
    filename = get_filename(full_path)
    return database.insert_file(filename, file_hash, status.value)
