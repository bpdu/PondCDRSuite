import logging
import sys

import database
import utils


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    database.init_db()

    try:
        cdr_folder, items = utils.get_files()
    except Exception:
        logging.exception("Failed to get files")
        return 2

    logging.info("Starting CDR notify")
    logging.info("Scanning folder: %s", cdr_folder)

    for filename, full_path in items:
        try:
            file_hash = utils.calculate_hash(full_path)
        except Exception:
            logging.exception("Failed to calculate hash for %s", filename)
            continue

        if utils.get_hash(file_hash):
            continue

        if not utils.send_email(full_path, filename=filename):
            logging.error("Failed to send email for %s", filename)
            continue

        utils.set_hash(filename, file_hash, utils.FileStatus.SENT)
        logging.info("File processed successfully: %s", filename)

    return 0


if __name__ == "__main__":
    sys.exit(main())