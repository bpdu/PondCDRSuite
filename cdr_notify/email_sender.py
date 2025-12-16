import logging
import smtplib
from email.message import EmailMessage

import utils


def send_email(full_path: str) -> bool:
    try:
        config = utils.load_config()

        smtp_host = config.get("SMTP_HOST", "").strip()
        smtp_port_str = config.get("SMTP_PORT", "587").strip() or "587"
        smtp_port = int(smtp_port_str)

        email_from = config.get("EMAIL_FROM", "").strip()
        email_to = config.get("EMAIL_TO", "").strip()

        smtp_user = config.get("SMTP_USER", "").strip()
        smtp_password = config.get("SMTP_PASSWORD", "").strip()

        if not smtp_host:
            raise RuntimeError("SMTP_HOST is not set in config/config.txt")
        if not email_from:
            raise RuntimeError("EMAIL_FROM is not set in config/config.txt")
        if not email_to:
            raise RuntimeError("EMAIL_TO is not set in config/config.txt")

        n = utils.build_notification(full_path)

        msg = EmailMessage()
        msg["Subject"] = n["subject"]
        msg["From"] = email_from
        msg["To"] = email_to
        msg.set_content(n["body"])

        with open(full_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="text",
                subtype="plain",
                filename=n["filename"],
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
        logging.exception("Failed to send email for file %s", utils.get_filename(full_path))
        return False
