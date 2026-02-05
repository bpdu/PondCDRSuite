from __future__ import annotations

import logging

from . import database
from . import email_sender
from . import telegram_sender
from . import utils


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
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

    new_files = [f for f in utils.get_files(cdr_folder) if not utils.is_known_file(f)]

    if not new_files:
        logging.info("No new CDR files found")
        return

    for full_path in new_files:
        file_hash = utils.calculate_hash(full_path)
        if not file_hash:
            logging.error("Failed to calculate hash for %s", full_path)
            continue

        notification = utils.build_notification(full_path)

        if send_email:
            email_sender.send_email(full_path, notification, config)
        if send_telegram:
            telegram_sender.send_message(notification, config)

        utils.insert_file_record(full_path, file_hash, utils.FileStatus.SENT)
        logging.info("File processed successfully: %s", utils.get_filename(full_path))


if __name__ == "__main__":
    main()
