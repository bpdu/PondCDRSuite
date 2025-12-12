import logging
import os
import time

import database
import utils


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    cdr_folder = os.environ.get("CDR_FOLDER", "").strip()
    if not cdr_folder:
        raise RuntimeError("CDR_FOLDER is not set")

    check_interval = int(os.environ.get("CHECK_INTERVAL", "3600"))

    database.init_db()

    logging.info("Starting CDR notify service")
    logging.info("Watching folder: %s", cdr_folder)

    while True:
        try:
            files = os.listdir(cdr_folder)
        except Exception:
            logging.exception("Failed to list directory %s", cdr_folder)
            time.sleep(check_interval)
            continue

        for filename in files:
            full_path = os.path.join(cdr_folder, filename)

            if not os.path.isfile(full_path):
                continue

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

        time.sleep(check_interval)


if __name__ == "__main__":
    main()
