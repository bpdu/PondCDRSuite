import logging

import requests

import utils


def send_new_file(full_path: str) -> bool:
    try:
        config = utils.load_config()

        token = config.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = config.get("TELEGRAM_CHAT_ID", "").strip()

        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in secrets/tlgrm.env")
        if not chat_id:
            raise RuntimeError("TELEGRAM_CHAT_ID is not set in secrets/tlgrm.env")

        filename = utils.get_filename(full_path)
        text = f"New CDR file arrived: {filename}"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }

        r = requests.post(url, json=payload, timeout=15)
        if not r.ok:
            raise RuntimeError(f"Telegram API error {r.status_code}: {r.text}")

        return True

    except Exception:
        logging.exception("Failed to send telegram notification for %s", utils.get_filename(full_path))
        return False
