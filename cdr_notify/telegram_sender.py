from __future__ import annotations

import logging

import requests


def send_message(notification: dict[str, str], config: dict[str, str]) -> bool:
    try:
        token = config.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = config.get("TELEGRAM_CHAT_ID", "").strip()

        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
        if not chat_id:
            raise RuntimeError("TELEGRAM_CHAT_ID is not set")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": notification["telegram_text"],
        }

        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()

        return True

    except Exception:
        logging.exception(
            "Failed to send telegram message for %s", notification["filename"]
        )
        return False
