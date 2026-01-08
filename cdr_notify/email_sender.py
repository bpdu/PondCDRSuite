
import logging
import smtplib
from email.message import EmailMessage

import utils
from utils import NotificationError


@utils.retry(max_attempts=3)
def send_email(file_path: str, config: dict[str, str]) -> bool:
    """
    Send email notification for a file.

    Args:
        file_path: Full path to the CDR file
        config: Configuration dictionary

    Returns:
        True if email sent successfully

    Raises:
        NotificationError: If email sending fails
    """
    try:
        smtp_host = config["SMTP_HOST"].strip()
        smtp_port = int(config.get("SMTP_PORT", "587").strip() or "587")
        smtp_user = config.get("SMTP_USER", "").strip()
        smtp_password = config.get("SMTP_PASSWORD", "").strip()
        email_from = config["EMAIL_FROM"].strip()
        email_to = config["EMAIL_TO"].strip()

        n = utils.build_notification(file_path)

        msg = EmailMessage()
        msg["Subject"] = n["subject"]
        msg["From"] = email_from
        msg["To"] = email_to
        msg.set_content(n["body"])

        with open(file_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="text",
                subtype="plain",
                filename=n["filename"],
            )

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logging.info(f"Email sent successfully for {n['filename']}")
        return True

    except Exception as e:
        raise NotificationError(f"Email sending failed: {e}")
