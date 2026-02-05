from __future__ import annotations

import logging
import time

import database
import email_sender
import telegram_sender
import utils


def main() -> None:
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M GMT",
    )

    config = utils.load_config()

    cdr_folder = config.get("CDR_FOLDER", "").strip()
    if not cdr_folder:
        raise RuntimeError(f"CDR_FOLDER is not set in {utils.CONFIG_PATH}")

    db_name = config.get("DB_NAME", "cdr_files.db").strip() or "cdr_files.db"
    database.init_db(db_name)
    send_email = utils.is_enabled(config.get("EMAIL_SEND", ""))
    send_telegram = utils.is_enabled(config.get("TELEGRAM_SEND", ""))
    logging.info("Starting CDR notify service")

    processed = 0
    for full_path in utils.get_files(cdr_folder):
        file_hash = utils.calculate_hash(full_path)
        if not file_hash:
            logging.error("Failed to calculate hash for %s", full_path)
            continue

        if utils.is_known_hash(file_hash):
            continue

        notification = utils.build_notification(full_path)

        email_ok = True
        telegram_ok = True
        if send_email:
            email_ok = email_sender.send_email(full_path, notification, config)
        if send_telegram:
            telegram_ok = telegram_sender.send_message(full_path, notification, config)

        if not email_ok or not telegram_ok:
            logging.warning("Skipping DB record for %s due to send failure", utils.get_filename(full_path))
            continue

        if not utils.insert_file_record(full_path, file_hash, utils.FileStatus.SENT):
            logging.error("Failed to save DB record for %s", utils.get_filename(full_path))
            continue

        logging.info("File processed successfully: %s", utils.get_filename(full_path))
        processed += 1

    if not processed:
        logging.info("No new CDR files found")


if __name__ == "__main__":
    main()
