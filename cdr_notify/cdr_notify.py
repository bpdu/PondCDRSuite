import logging
import os

import database
import email_sender
import telegram_sender
import utils


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = utils.load_config()

    cdr_folder = config.get("CDR_FOLDER", "").strip()
    if not cdr_folder:
        raise RuntimeError(f"CDR_FOLDER is not set in {utils.CONFIG_PATH}")

    db_name = config.get("DB_NAME", "").strip()
    if db_name:
        os.environ["DB_NAME"] = db_name

    database.init_db()
    logging.info("Starting CDR notify service")

    files = utils.get_files(cdr_folder)
    found_new_files = False

    for full_path in files:
        if utils.is_known_file(full_path):
            continue

        found_new_files = True

        file_hash = utils.calculate_hash(full_path)
        if not file_hash:
            logging.error("Failed to calculate hash for %s", full_path)
            continue

        utils.insert_file_record(full_path, file_hash, utils.FileStatus.ARRIVED, "")

        telegram_sender.send_message(full_path)
        email_sender.send_email(full_path)

        utils.update_file_status(full_path, utils.FileStatus.SENT, "")
        logging.info("File processed successfully: %s", utils.get_filename(full_path))

    if not found_new_files:
        logging.info("No new CDR files found")


if __name__ == "__main__":
    main()
