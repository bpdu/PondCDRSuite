
import logging

import requests

import utils


def send_message(full_path: str) -> bool:
    try:
        config = utils.load_config()

        if not utils.is_enabled(config.get("TELEGRAM_SEND", "")):
            return True

        token = config.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = config.get("TELEGRAM_CHAT_ID", "").strip()

        if not token:
            raise RuntimeError(f"TELEGRAM_BOT_TOKEN is not set in {utils.TELEGRAM_ENV_PATH}")
        if not chat_id:
            raise RuntimeError(f"TELEGRAM_CHAT_ID is not set in {utils.TELEGRAM_ENV_PATH}")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": utils.build_notification(full_path)["telegram_text"],
        }

        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()

        return True

    except Exception:
        logging.exception("Failed to send telegram message for %s", utils.get_filename(full_path))
        return False
