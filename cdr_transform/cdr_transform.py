#!/usr/bin/env python3
import os
import sys
import shutil
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
CDR_LOG_FILE = os.path.join(LOG_DIR, "cdr_transform_cdr.log")
LU_LOG_FILE = os.path.join(LOG_DIR, "cdr_transform_lu.log")

# Hardcoded paths as per task requirements
INBOUND_BASE = "/home/cdr_admin/inbound"
OUTBOUND_BASE = "/home/cdr_admin/outbound"


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


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def build_dest_path(dest_dir: str, file_type: str, filename: str) -> str:
    """Build destination path with flat structure (no client subdirectories)."""
    return os.path.join(dest_dir, file_type, filename)


def should_copy(source_path: str, dest_path: str) -> bool:
    """Check if file should be copied using SHA256 hash comparison."""
    if not os.path.exists(dest_path):
        return True
    return calculate_sha256(source_path) != calculate_sha256(dest_path)


def copy_atomically(source_path: str, dest_path: str) -> bool:
    """Copy file atomically using temporary file."""
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
    """Process a single file: copy to destination with flat structure."""
    file_type = get_file_type(filename)

    if not file_type:
        return "ignored", 0

    logger = get_logger(file_type, cdr_logger, lu_logger)
    dest_path = build_dest_path(dest_dir, file_type, filename)
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
    """Scan source directory and process all CSV files."""
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


def validate_args(file_type: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Validate CLI argument and return paths."""
    if file_type not in ("cdr", "lu"):
        return False, f"Invalid file type: {file_type}. Must be 'cdr' or 'lu'", None, None

    source_dir = os.path.join(INBOUND_BASE, f"telna_{file_type}")
    dest_dir = OUTBOUND_BASE

    if not os.path.exists(source_dir):
        return False, f"Source directory does not exist: {source_dir}", None, None

    if not os.path.isdir(source_dir):
        return False, f"Source path is not a directory: {source_dir}", None, None

    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create destination directory: {dest_dir}: {e}", None, None

    if not os.path.isdir(dest_dir):
        return False, f"Destination path is not a directory: {dest_dir}", None, None

    if not os.access(dest_dir, os.W_OK):
        return False, f"Destination directory is not writable: {dest_dir}", None, None

    return True, None, source_dir, dest_dir


def log_summary(copied: int, skipped: int, overwritten: int, errors: int, cdr_logger, lu_logger):
    """Log execution summary to both loggers."""
    cdr_logger.info(f"RUN SUMMARY: copied={copied} skipped={skipped} overwritten={overwritten} errors={errors}")
    lu_logger.info(f"RUN SUMMARY: copied={copied} skipped={skipped} overwritten={overwritten} errors={errors}")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <cdr|lu>", file=sys.stderr)
        sys.exit(1)

    file_type = sys.argv[1]

    valid, error, source_dir, dest_dir = validate_args(file_type)
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
