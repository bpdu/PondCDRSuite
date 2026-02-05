from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from . import utils


def send_email(
    full_path: str, notification: dict[str, str], config: dict[str, str]
) -> bool:
    try:
        smtp_host = config.get("SMTP_HOST", "").strip()
        smtp_port = int(config.get("SMTP_PORT", "587").strip() or "587")
        email_from = config.get("EMAIL_FROM", "").strip()
        email_to = config.get("EMAIL_TO", "").strip()
        smtp_user = config.get("SMTP_USER", "").strip()
        smtp_password = config.get("SMTP_PASSWORD", "").strip()

        if not smtp_host:
            raise RuntimeError(f"SMTP_HOST is not set in {utils.CONFIG_PATH}")
        if not email_from:
            raise RuntimeError(f"EMAIL_FROM is not set in {utils.CONFIG_PATH}")
        if not email_to:
            raise RuntimeError(f"EMAIL_TO is not set in {utils.CONFIG_PATH}")

        msg = EmailMessage()
        msg["Subject"] = notification["subject"]
        msg["From"] = email_from
        msg["To"] = email_to
        msg.set_content(notification["body"])

        with open(full_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="text",
                subtype="plain",
                filename=notification["filename"],
            )

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)

        return True

    except Exception:
        logging.exception(
            "Failed to send email for file %s", notification["filename"]
        )
        return False
