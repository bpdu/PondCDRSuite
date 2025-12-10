from enum import Enum
import hashlib
import logging
import os
import smtplib
import sqlite3
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import database


# Hash length in hex characters; 64 = full SHA-256
HASH_LENGTH: int = 64

# SMTP and notification configuration (constants as requested)
SMTP_SERVER: str = "smtp.example.com"
SMTP_PORT: int = 587
SMTP_FROM: str = "alerts@example.com"
EMAIL_TO_SEND: str = "alerts@example.com"
SMTP_USE_TLS: bool = True
SMTP_USE_SSL: bool = False

BASE_DIR: Path = Path(__file__).resolve().parent
RESOURCES_DIR: Path = BASE_DIR / "resources"


class FileStatus(Enum):
    ARRIVED = "Arrived"
    SENT = "Sent"
    DELIVERED = "Delivered"
    REMOVED = "Removed"


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

def _read_resource(name: str) -> str:
    """
    Read a text file from the resources directory.

    Raises:
        FileNotFoundError if the file does not exist.
        RuntimeError for any I/O error during reading.
    """
    path = RESOURCES_DIR / name
    if not path.is_file():
        message = f"Resource file not found: {path}"
        logging.error(message)
        raise FileNotFoundError(message)

    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        logging.exception("Failed to read resource file '%s': %s", path, e)
        raise RuntimeError(f"Failed to read resource file: {path}") from e


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------

def calculate_hash(filename: str) -> str:
    """
    Accept a file path and return a deterministic SHA-256 hash of its content.
    """
    path = Path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hashing: {path}")

    sha256 = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    digest = sha256.hexdigest()
    return digest[:HASH_LENGTH] if HASH_LENGTH > 0 else digest


# ---------------------------------------------------------------------------
# Database-related helpers
# ---------------------------------------------------------------------------

def get_hash(file_hash: str) -> Optional[sqlite3.Row]:
    """
    Accept a hash and return the corresponding row from the database.
    """
    return database.fetch_by_hash(file_hash)


def set_hash(filename: str, status: FileStatus) -> int:
    """
    Accept a file path, calculate its content hash and add it to the database.
    Only the filename (basename) is stored in the database.
    Returns the inserted record id.
    """
    file_hash = calculate_hash(filename)
    basename = Path(filename).name
    return database.insert_record(basename, file_hash, status.value)


def update_status(file_hash: str, status: FileStatus) -> bool:
    """
    Accept a hash and a new status. Return True on success.
    """
    return database.update_status(file_hash, status.value)


# ---------------------------------------------------------------------------
# Email helper
# ---------------------------------------------------------------------------

def send_email(filename: str) -> bool:
    """
    Accept a file path and send an email with the file attached.
    Return True on success, False on failure.
    """
    smtp_user = os.getenv("SMTP_USERNAME", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")

    basename = Path(filename).name

    # Load templates; errors must stop the application
    subject_template = _read_resource("email_subject.txt")
    body_template = _read_resource("email_body.txt")

    context = {"filename": basename}
    subject = subject_template.format(**context).strip()
    body = body_template.format(**context)

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = EMAIL_TO_SEND
    msg.attach(MIMEText(body, _charset="utf-8"))

    # Attach file if it exists
    path = Path(filename)
    if path.is_file():
        try:
            with path.open("rb") as f:
                part = MIMEApplication(f.read(), Name=path.name)
            part["Content-Disposition"] = f'attachment; filename="{path.name}"'
            msg.attach(part)
        except OSError as e:
            logging.warning("Failed to attach file '%s': %s", filename, e)

    logging.info(
        "Sending email about file '%s' to '%s' via %s:%s",
        basename,
        EMAIL_TO_SEND,
        SMTP_SERVER,
        SMTP_PORT,
    )

    try:
        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)

        with server:
            server.ehlo()
            if SMTP_USE_TLS and not SMTP_USE_SSL:
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logging.info("Email sent successfully for file '%s'", basename)
        return True
    except Exception as e:
        logging.exception("Failed to send email for file '%s': %s", basename, e)
        return False
