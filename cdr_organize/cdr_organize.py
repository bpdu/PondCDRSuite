#!/usr/bin/env python3
import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
CDR_LOG_FILE = os.path.join(LOG_DIR, "cdr_process.log")
LU_LOG_FILE = os.path.join(LOG_DIR, "lu_process.log")


def setup_loggers():
    os.makedirs(LOG_DIR, exist_ok=True)

    cdr_logger = logging.getLogger('cdr')
    cdr_logger.setLevel(logging.INFO)
    cdr_handler = logging.FileHandler(CDR_LOG_FILE)
    cdr_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
    cdr_logger.addHandler(cdr_handler)

    lu_logger = logging.getLogger('lu')
    lu_logger.setLevel(logging.INFO)
    lu_handler = logging.FileHandler(LU_LOG_FILE)
    lu_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
    lu_logger.addHandler(lu_handler)

    return cdr_logger, lu_logger


def get_logger(file_type: str, cdr_logger, lu_logger):
    if file_type == "cdr":
        return cdr_logger
    elif file_type == "lu":
        return lu_logger
    return None


def get_file_type(filename: str) -> Optional[str]:
    if "_CDR_" in filename:
        return "cdr"
    elif "_LU_" in filename:
        return "lu"
    return None


def extract_client(filename: str) -> Optional[str]:
    prefix = filename.startswith("LIVE_")
    if not prefix:
        return None

    after_prefix = filename[5:]
    cdr_pos = after_prefix.find("_CDR_")
    lu_pos = after_prefix.find("_LU_")

    if cdr_pos != -1:
        return after_prefix[:cdr_pos]
    elif lu_pos != -1:
        return after_prefix[:lu_pos]
    return None


def parse_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    file_type = get_file_type(filename)
    client = extract_client(filename) if file_type else None
    return file_type, client


def build_dest_path(dest_dir: str, file_type: str, client: str, filename: str) -> str:
    return os.path.join(dest_dir, file_type, client, filename)


def should_copy(source_path: str, dest_path: str) -> bool:
    if not os.path.exists(dest_path):
        return True
    return os.path.getsize(source_path) != os.path.getsize(dest_path)


def copy_atomically(source_path: str, dest_path: str) -> bool:
    temp_path = dest_path + ".tmp"
    dest_dir = os.path.dirname(dest_path)

    try:
        shutil.copy2(source_path, temp_path)
        os.rename(temp_path, dest_path)
        return True
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
        raise e


def process_file(source_path: str, dest_dir: str, filename: str, cdr_logger, lu_logger) -> Tuple[str, int]:
    file_type, client = parse_filename(filename)

    if not file_type or not client:
        return "ignored", 0

    logger = get_logger(file_type, cdr_logger, lu_logger)
    dest_path = build_dest_path(dest_dir, file_type, client, filename)
    dest_dir_full = os.path.dirname(dest_path)

    try:
        os.makedirs(dest_dir_full, exist_ok=True)
    except Exception as e:
        logger.error(f"ERROR {filename}: cannot create directory {dest_dir_full}: {e}")
        return "error", 1

    if not should_copy(source_path, dest_path):
        logger.info(f"SKIPPED {filename}")
        return "skipped", 0

    try:
        dest_exists = os.path.exists(dest_path)
        copy_atomically(source_path, dest_path)

        if dest_exists:
            logger.info(f"OVERWRITTEN {filename}")
            return "overwritten", 0
        else:
            logger.info(f"COPIED {filename}")
            return "copied", 0
    except Exception as e:
        logger.error(f"ERROR {filename}: {e}")
        return "error", 1


def scan_directory(source_dir: str, dest_dir: str, cdr_logger, lu_logger) -> Tuple[int, int, int, int]:
    copied = 0
    skipped = 0
    overwritten = 0
    errors = 0

    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            if not filename.lower().endswith('.csv'):
                continue

            source_path = os.path.join(root, filename)
            status, err = process_file(source_path, dest_dir, filename, cdr_logger, lu_logger)

            if status == "copied":
                copied += 1
            elif status == "skipped":
                skipped += 1
            elif status == "overwritten":
                overwritten += 1
            elif status == "error":
                errors += err

    return copied, skipped, overwritten, errors


def validate_args(source_dir: str, dest_dir: str) -> Tuple[bool, Optional[str]]:
    if not os.path.exists(source_dir):
        return False, f"Source directory does not exist: {source_dir}"

    if not os.path.isdir(source_dir):
        return False, f"Source path is not a directory: {source_dir}"

    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create destination directory: {dest_dir}: {e}"

    if not os.path.isdir(dest_dir):
        return False, f"Destination path is not a directory: {dest_dir}"

    if not os.access(dest_dir, os.W_OK):
        return False, f"Destination directory is not writable: {dest_dir}"

    return True, None


def log_summary(copied: int, skipped: int, overwritten: int, errors: int, cdr_logger, lu_logger):
    cdr_logger.info(f"RUN SUMMARY: copied={copied} skipped={skipped} overwritten={overwritten} errors={errors}")
    lu_logger.info(f"RUN SUMMARY: copied={copied} skipped={skipped} overwritten={overwritten} errors={errors}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <SOURCE_DIR> <DEST_DIR>", file=sys.stderr)
        sys.exit(1)

    source_dir = sys.argv[1]
    dest_dir = sys.argv[2]

    valid, error = validate_args(source_dir, dest_dir)
    if not valid:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    cdr_logger, lu_logger = setup_loggers()

    copied, skipped, overwritten, errors = scan_directory(source_dir, dest_dir, cdr_logger, lu_logger)

    log_summary(copied, skipped, overwritten, errors, cdr_logger, lu_logger)

    if errors > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
