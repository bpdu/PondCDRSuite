import hashlib
import logging
import os
from enum import Enum

import database


class FileStatus(Enum):
    ARRIVED = "ARRIVED"
    SENT = "SENT"


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_BASE_DIR, "config", "config.txt")
_RESOURCES_DIR = os.path.join(_BASE_DIR, "resources")


def load_config() -> dict[str, str]:
    config: dict[str, str] = {}

    if not os.path.isfile(_CONFIG_PATH):
        raise RuntimeError("config/config.txt not found")

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
                value = value[1:-1]

            config[key] = value

    return config


def load_template(filename: str) -> str:
    path = os.path.join(_RESOURCES_DIR, filename)
    if not os.path.isfile(path):
        raise RuntimeError(f"Template not found: {filename}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_filename(full_path: str) -> str:
    return os.path.basename(full_path)


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
