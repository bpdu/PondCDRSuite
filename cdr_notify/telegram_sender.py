from __future__ import annotations

import logging

import requests


def send_message(full_path: str, notification: dict[str, str], config: dict[str, str]) -> bool:
    try:
        token = config.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = config.get("TELEGRAM_CHAT_ID", "").strip()

        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
        if not chat_id:
            raise RuntimeError("TELEGRAM_CHAT_ID is not set")

        url = f"https://api.telegram.org/bot{token}/sendDocument"

        with open(full_path, "rb") as f:
            r = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "caption": notification["telegram_text"],
                    "parse_mode": "HTML",
                },
                files={"document": (notification["filename"], f)},
                timeout=30,
            )

        r.raise_for_status()
        return True

    except Exception:
        logging.exception(
            "Failed to send telegram message for %s", notification["filename"]
        )
        return False
