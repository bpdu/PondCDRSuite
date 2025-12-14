import hashlib
import logging
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from enum import Enum
from pathlib import Path
from typing import List, Optional

import database


class FileStatus(Enum):
    ARRIVED = "ARRIVED"
    SENT = "SENT"


def get_files(cdr_folder: str) -> List[str]:
    cdr_folder = (cdr_folder or "").strip()
    if not cdr_folder:
        raise RuntimeError("CDR_FOLDER is not set")

    folder = Path(cdr_folder)
    if not folder.exists():
        raise RuntimeError(f"CDR_FOLDER does not exist: {cdr_folder}")
    if not folder.is_dir():
        raise RuntimeError(f"CDR_FOLDER is not a directory: {cdr_folder}")

    logging.info("Scanning folder: %s", cdr_folder)

    try:
        names = os.listdir(cdr_folder)
    except Exception:
        logging.exception("Failed to list directory %s", cdr_folder)
        raise

    result: List[str] = []
    for name in names:
        if name.startswith("."):
            continue

        full_path = folder / name
        if not full_path.is_file():
            continue

        result.append(str(full_path))

    return result


def calculate_hash(path: str) -> Optional[str]:
    try:
        file_path = Path(path)
        if not file_path.is_file():
            return None

        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    except Exception:
        logging.exception("Failed to calculate hash for %s", path)
        return None


def get_hash(file_hash: str) -> bool:
    try:
        return database.get_file_by_hash(file_hash) is not None
    except Exception:
        logging.exception("Database read error")
        return False


def set_hash(filename: str, file_hash: str, status: FileStatus) -> bool:
    try:
        return database.insert_file(filename, file_hash, status.value)
    except Exception:
        logging.exception("Database insert error")
        return False


def update_status(file_hash: str, status: FileStatus) -> bool:
    try:
        return database.update_status(file_hash, status.value)
    except Exception:
        logging.exception("Database update error")
        return False


def send_email(filepath: str) -> bool:
    try:
        file_path = Path(filepath)
        filename = file_path.name

        smtp_host = os.environ.get("SMTP_HOST", "").strip()
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "").strip()
        smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()

        email_from = os.environ.get("EMAIL_FROM", "").strip()
        email_to = os.environ.get("EMAIL_TO_SEND", "").strip()

        if not smtp_host:
            raise RuntimeError("SMTP_HOST is not set")
        if not email_from:
            raise RuntimeError("EMAIL_FROM is not set")
        if not email_to:
            raise RuntimeError("EMAIL_TO_SEND is not set")

        resources_dir = Path(__file__).parent / "resources"
        subject_template = (resources_dir / "email_subject.txt").read_text().strip()
        body_template = (resources_dir / "email_body.txt").read_text()

        changed_ts = datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        subject = subject_template.format(filename=filename)
        body = body_template.format(filename=filename, changed=changed_ts)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = email_to
        msg.set_content(body)

        # Timlead request: keep attachment logic simple for text files
        with open(file_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="text",
                subtype="plain",
                filename=filename,
            )

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True

    except Exception:
        logging.exception("Failed to send email for file %s", filepath)
        return False