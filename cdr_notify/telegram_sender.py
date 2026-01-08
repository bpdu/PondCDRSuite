
import logging

import requests

import utils
from utils import NotificationError


@utils.retry(max_attempts=3)
def send_telegram(file_path: str, config: dict[str, str]) -> bool:
    """
    Send Telegram notification for a file.

    Args:
        file_path: Full path to the CDR file
        config: Configuration dictionary

    Returns:
        True if message sent or Telegram disabled

    Raises:
        NotificationError: If Telegram sending fails
    """
    enabled = config.get("TELEGRAM_SEND", "").strip().lower() == "true"
    if not enabled:
        logging.debug("Telegram sending disabled, skipping")
        return True

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

    except requests.RequestException as e:
        raise NotificationError(f"Telegram sending failed: {e}")
    except Exception as e:
        raise NotificationError(f"Unexpected error sending Telegram: {e}")
