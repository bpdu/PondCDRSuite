# cdr_notify.py

import logging
import os

import database
import utils
from email_sender import EmailSender
from telegram_sender import TelegramSender
from utils import ConfigError, NotificationError, FileStatus


class NotificationResult:
    """Encapsulates the result of sending notifications"""

    def __init__(self, email_sent: bool, telegram_sent: bool, errors: list[str]):
        self.email_sent = email_sent
        self.telegram_sent = telegram_sent
        self.errors = errors

    @property
    def status(self) -> FileStatus:
        """Determine overall status"""
        if self.email_sent and self.telegram_sent:
            return FileStatus.SENT
        elif self.email_sent or self.telegram_sent:
            return FileStatus.PARTIAL_SUCCESS
        else:
            return FileStatus.FAILED

    @property
    def error_message(self) -> str | None:
        """Get concatenated error messages"""
        return "; ".join(self.errors) if self.errors else None


class CDRNotifyService:
    """Main service for processing and notifying about CDR files"""

    def __init__(self, config: dict[str, str]):
        self.config = config
        self.cdr_folder = self._validate_cdr_folder()
        self._setup_database()

        # Initialize notification senders with dependency injection
        self.email_sender = EmailSender(config)
        self.telegram_sender = TelegramSender(config)

    def _validate_cdr_folder(self) -> str:
        """Validate CDR_FOLDER configuration"""
        cdr_folder = self.config.get("CDR_FOLDER", "").strip()
        if not cdr_folder:
            raise ConfigError(f"CDR_FOLDER is not set in {utils.CONFIG_PATH}")
        if not os.path.isdir(cdr_folder):
            raise ConfigError(f"CDR_FOLDER does not exist: {cdr_folder}")
        return cdr_folder

    def _setup_database(self) -> None:
        """Setup database with custom DB_NAME if specified"""
        db_name = self.config.get("DB_NAME", "").strip()
        if db_name:
            os.environ["DB_NAME"] = db_name
        database.init_db()

    def process_file(self, full_path: str) -> None:
        """
        Process a single CDR file: send notifications and record in DB.

        This is the critical method that fixes the bug where files were not
        saved to DB on partial failure.
        """
        filename = utils.get_filename(full_path)

        # Calculate file hash
        file_hash = utils.calculate_hash(full_path)
        if not file_hash:
            logging.error(f"Failed to calculate hash for {filename}, skipping")
            return

        # Send notifications (with retries)
        result = self._send_notifications(full_path)

        # CRITICAL: Always save to database, regardless of notification result
        # This fixes the bug where failed notifications caused infinite reprocessing
        try:
            utils.insert_file_record(
                full_path=full_path,
                file_hash=file_hash,
                status=result.status,
                email_sent=result.email_sent,
                telegram_sent=result.telegram_sent,
                error_message=result.error_message,
                retry_count=3 if result.errors else 0
            )

            # Log result
            if result.status == FileStatus.SENT:
                logging.info(f"File processed successfully: {filename}")
            elif result.status == FileStatus.PARTIAL_SUCCESS:
                logging.warning(
                    f"Partial success for {filename}: "
                    f"email={'OK' if result.email_sent else 'FAILED'}, "
                    f"telegram={'OK' if result.telegram_sent else 'FAILED'}"
                )
            else:
                logging.error(f"All notifications failed for {filename}: {result.error_message}")

        except Exception as e:
            logging.error(f"Failed to save {filename} to database: {e}")
            # Note: File will be reprocessed on next run, but this is acceptable
            # since it's a database failure, not a notification failure

    def _send_notifications(self, full_path: str) -> NotificationResult:
        """
        Send both email and Telegram notifications.

        Returns NotificationResult with status of each channel.
        Catches exceptions from senders and records them.
        """
        email_sent = False
        telegram_sent = False
        errors = []

        # Try email
        try:
            email_sent = self.email_sender.send(full_path)
        except NotificationError as e:
            errors.append(f"Email: {e}")
            logging.error(f"Email notification failed for {utils.get_filename(full_path)}: {e}")

        # Try Telegram (independent of email result)
        try:
            telegram_sent = self.telegram_sender.send(full_path)
        except NotificationError as e:
            errors.append(f"Telegram: {e}")
            logging.error(f"Telegram notification failed for {utils.get_filename(full_path)}: {e}")

        return NotificationResult(email_sent, telegram_sent, errors)

    def run(self) -> None:
        """Main run loop: process all new files in CDR folder"""
        logging.info("Starting CDR notify service")

        files = utils.get_files(self.cdr_folder)
        new_files = [f for f in files if not utils.is_known_file(f)]

        if not new_files:
            logging.info("No new CDR files found")
            return

        logging.info(f"Found {len(new_files)} new file(s) to process")

        for full_path in new_files:
            self.process_file(full_path)


def main() -> None:
    """Application entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        # Load and validate configuration at startup
        config = utils.load_config()

        # Run service
        service = CDRNotifyService(config)
        service.run()

    except ConfigError as e:
        logging.error(f"Configuration error: {e}")
        exit(1)
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
