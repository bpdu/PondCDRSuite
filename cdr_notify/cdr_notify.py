import logging
import os

import database
import utils
import email


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    cdr_folder = os.environ.get("CDR_FOLDER", "").strip()
    if not cdr_folder:
        raise RuntimeError("CDR_FOLDER is not set")

    database.init_db()

    logging.info("Starting CDR notify service")

    files = utils.get_files(cdr_folder)

    for full_path in files:
        file_hash = utils.calculate_hash(full_path)
        if not file_hash:
            continue

        if utils.get_hash(file_hash):
            continue

        if not email.send_email(full_path):
            continue

        filename = os.path.basename(full_path)
        utils.set_hash(filename, file_hash, utils.FileStatus.SENT)

        logging.info("File processed successfully: %s", filename)


if __name__ == "__main__":
    main()
