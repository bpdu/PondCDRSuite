import logging

import database
import email_sender
import telegram_notify
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

        if not email_sender.send_email(full_path):
            continue

        telegram_notify.send_new_file(full_path)

        utils.set_hash(full_path, file_hash, utils.FileStatus.SENT)
        logging.info("File processed successfully: %s", utils.get_filename(full_path))


if __name__ == "__main__":
    main()
