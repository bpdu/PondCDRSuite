import hashlib
import logging
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from enum import Enum

import database


class FileStatus(Enum):
    ARRIVED = "ARRIVED"
    SENT = "SENT"


def calculate_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


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


def send_email(filepath: str, filename: str) -> bool:
    try:
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

        msg = EmailMessage()
        msg["Subject"] = f"New CDR file received: {filename}"
        msg["From"] = email_from
        msg["To"] = email_to

        msg.set_content(
            "A new CDR file has been received.\n"
            f"File: {filename}\n"
        )

        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type:
            maintype, subtype = mime_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"

        with open(filepath, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
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
        logging.exception("Failed to send email for file %s", filename)
        return False
