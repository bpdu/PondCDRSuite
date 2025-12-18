import logging
import sys

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
        raise RuntimeError("CDR_FOLDER is not set in config/config.txt")

    database.init_db()

    logging.info("Starting CDR notify service")

    files = utils.get_files(cdr_folder)

    for full_path in files:
        file_hash = utils.calculate_hash(full_path)
        if not file_hash:
            continue

        if utils.get_hash(file_hash):
            continue

        email_send = config.get("EMAIL_SEND", "").strip()
        telegram_send = config.get("TELEGRAM_SEND", "").strip()
        if telegram_send:
            telegram_send_status = telegram_sender.send_message(full_path)
        if email_send:
            email_send_status = email_sender.send_email(full_path)


        if email_send_status or telegram_send_status:
            utils.set_hash(full_path, file_hash, utils.FileStatus.SENT)
            logging.info(
                "File processed successfully: %s (email=%s telegram=%s)",
                utils.get_filename(full_path),
                email_send_status,
                telegram_send_status,
            )
            sys.exit()

    logging.info("No new CDR files found")


if __name__ == "__main__":
    main()
