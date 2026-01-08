
import logging
from typing import Dict

import requests

import utils
from utils import NotificationError, ConfigError


class TelegramSender:
    """Handles Telegram notifications via Bot API"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.enabled = utils.is_enabled(config.get("TELEGRAM_SEND", ""))

        if self.enabled:
            self._validate_config()

    def _validate_config(self) -> None:
        """Validate required Telegram configuration"""
        required = {
            "TELEGRAM_BOT_TOKEN": self.config.get("TELEGRAM_BOT_TOKEN", "").strip(),
            "TELEGRAM_CHAT_ID": self.config.get("TELEGRAM_CHAT_ID", "").strip(),
        }

        missing = [key for key, val in required.items() if not val]
        if missing:
            raise ConfigError(f"Missing required Telegram config: {', '.join(missing)}")

    @utils.retry(max_attempts=3)
    def send(self, full_path: str) -> bool:
        """
        Send Telegram notification for a file.

        Returns:
            True if message sent or Telegram disabled

        Raises:
            NotificationError: If Telegram sending fails
        """
        if not self.enabled:
            logging.debug("Telegram sending disabled, skipping")
            return True

        try:
            token = self.config["TELEGRAM_BOT_TOKEN"].strip()
            chat_id = self.config["TELEGRAM_CHAT_ID"].strip()

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": utils.build_notification(full_path)["telegram_text"],
            }

            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()

            logging.info(f"Telegram message sent for {utils.get_filename(full_path)}")
            return True

        except requests.RequestException as e:
            raise NotificationError(f"Telegram sending failed: {e}")
        except Exception as e:
            raise NotificationError(f"Unexpected error sending Telegram: {e}")
