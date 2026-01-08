
import logging
import smtplib
from email.message import EmailMessage
from typing import Dict

import utils
from utils import NotificationError, ConfigError


class EmailSender:
    """Handles email notifications with SMTP"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.enabled = config.get("EMAIL_SEND", "").strip().lower() == "true"

        # Validate config if enabled
        if self.enabled:
            self._validate_config()

    def _validate_config(self) -> None:
        """Validate required email configuration"""
        required = {
            "SMTP_HOST": self.config.get("SMTP_HOST", "").strip(),
            "EMAIL_FROM": self.config.get("EMAIL_FROM", "").strip(),
            "EMAIL_TO": self.config.get("EMAIL_TO", "").strip(),
        }

        missing = [key for key, val in required.items() if not val]
        if missing:
            raise ConfigError(f"Missing required email config: {', '.join(missing)}")

    @utils.retry(max_attempts=3)
    def send(self, full_path: str) -> bool:
        """
        Send email notification for a file.

        Returns:
            True if email sent or email disabled

        Raises:
            NotificationError: If email sending fails
        """
        if not self.enabled:
            logging.debug("Email sending disabled, skipping")
            return True

        try:
            smtp_host = self.config["SMTP_HOST"].strip()
            smtp_port = int(self.config.get("SMTP_PORT", "587").strip() or "587")
            smtp_user = self.config.get("SMTP_USER", "").strip()
            smtp_password = self.config.get("SMTP_PASSWORD", "").strip()
            email_from = self.config["EMAIL_FROM"].strip()
            email_to = self.config["EMAIL_TO"].strip()

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

        except (smtplib.SMTPException, OSError, IOError) as e:
            raise NotificationError(f"Email sending failed: {e}")
        except Exception as e:
            raise NotificationError(f"Unexpected error sending email: {e}")
