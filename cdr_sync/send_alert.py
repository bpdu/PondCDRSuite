#!/usr/bin/env python3
# send_alert.py - Send alerts via Telegram and/or Email

from __future__ import annotations

import argparse
import logging
import os
import smtplib
import sys
from email.message import EmailMessage

import requests
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] %(message)s",
)


def send_telegram(subject: str, message: str, token: str, chat_id: str) -> bool:
    try:
        text = f"*{subject}*\n\n{message}"
        r = requests.post(
            "https://api.telegram.org/bot%s/sendMessage" % token,
            data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=30,
        )
        if not r.ok:
            logging.error("Telegram API returned %d: %s", r.status_code, r.text)
            return False
        logging.info("Telegram alert sent")
        return True
    except Exception:
        logging.exception("Failed to send Telegram alert")
        return False


def send_email(
    subject: str,
    message: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from: str,
    smtp_to: str,
) -> bool:
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = smtp_to
        msg.set_content(message)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logging.info("Email alert sent to %s", smtp_to)
        return True
    except Exception:
        logging.exception("Failed to send email alert")
        return False


def is_true(value: str | None) -> bool:
    return value is not None and value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Send alerts via Telegram and/or Email")
    parser.add_argument("--subject", required=True, help="Alert subject")
    parser.add_argument("--message", required=True, help="Alert message")
    parser.add_argument("--telegram", default="false", help="Send via Telegram (true/false)")
    parser.add_argument("--email", default="false", help="Send via Email (true/false)")
    args = parser.parse_args()

    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.isfile(env_path):
        load_dotenv(env_path)

    success = True

    if is_true(args.telegram):
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat_id:
            logging.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
            success = False
        else:
            if not send_telegram(args.subject, args.message, token, chat_id):
                success = False

    if is_true(args.email):
        smtp_host = os.getenv("SMTP_HOST", "").strip()
        smtp_port = int(os.getenv("SMTP_PORT", "587").strip() or "587")
        smtp_user = os.getenv("SMTP_USER", "").strip()
        smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
        smtp_from = os.getenv("SMTP_FROM", "").strip()
        smtp_to = os.getenv("SMTP_TO", "").strip()

        if not smtp_host or not smtp_from or not smtp_to:
            logging.error("SMTP_HOST, SMTP_FROM, or SMTP_TO not set in .env")
            success = False
        else:
            if not send_email(
                args.subject,
                args.message,
                smtp_host,
                smtp_port,
                smtp_user,
                smtp_password,
                smtp_from,
                smtp_to,
            ):
                success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
