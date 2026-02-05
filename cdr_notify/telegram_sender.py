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

        with open(full_path, "rb") as f:
            r = requests.post(
                "https://api.telegram.org/bot%s/sendDocument" % token,
                data={
                    "chat_id": chat_id,
                    "caption": notification["telegram_text"],
                    "parse_mode": "HTML",
                },
                files={"document": (notification["filename"], f)},
                timeout=30,
            )

        if not r.ok:
            raise RuntimeError(f"Telegram API returned {r.status_code}")

        logging.info("Telegram message sent for %s", notification["filename"])
        return True

    except Exception:
        logging.exception(
            "Failed to send telegram message for %s", notification["filename"]
        )
        return False
