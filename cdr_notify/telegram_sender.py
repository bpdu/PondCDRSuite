
import logging
import time

import requests

import utils
from utils import NotificationError


def send_telegram(file_path: str, config: dict[str, str]) -> bool:
    """
    Send Telegram notification for a file with retry logic.

    Args:
        file_path: Full path to the CDR file
        config: Configuration dictionary

    Returns:
        True if message sent successfully

    Raises:
        NotificationError: If Telegram sending fails after 3 attempts
    """
    max_attempts = 3
    backoff_base = 2.0
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            token = config["TELEGRAM_BOT_TOKEN"].strip()
            chat_id = config["TELEGRAM_CHAT_ID"].strip()

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": utils.build_notification(file_path)["telegram_text"],
            }

            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()

            logging.info(f"Telegram message sent for {utils.get_filename(file_path)}")
            return True

        except Exception as e:
            last_exception = NotificationError(f"Telegram sending failed: {e}")
            if attempt < max_attempts:
                delay = backoff_base ** attempt
                logging.warning(
                    f"Telegram sending attempt {attempt}/{max_attempts} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logging.error(f"Telegram sending failed after {max_attempts} attempts: {e}")

    raise last_exception
