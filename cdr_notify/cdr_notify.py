#!/usr/bin/env python3

import logging
import os
from pathlib import Path

import database
import utils


CDR_FOLDER: str = os.getenv("CDR_FOLDER", "")


def process_cdr_folder() -> None:
    if not CDR_FOLDER:
        raise RuntimeError("CDR_FOLDER is not configured.")

    folder = Path(CDR_FOLDER).expanduser().resolve()

    if not folder.exists() or not folder.is_dir():
        raise RuntimeError(f"Invalid CDR_FOLDER path: {folder}")

    logging.info("Scanning CDR folder: %s", folder)

    for entry in sorted(folder.iterdir()):
        if not entry.is_file():
            continue

        filename = entry.name
        full_path = str(entry)

        # Hash is based on file content
        try:
            file_hash = utils.calculate_hash(full_path)
        except Exception:
            logging.exception("Failed to calculate hash for file '%s'", filename)
            continue

        try:
            existing = utils.get_hash(file_hash)
        except Exception:
            logging.exception("Database error while checking hash for '%s'", filename)
            continue

        if existing:
            logging.debug("Skipping existing file: %s", filename)
            continue

        logging.info("New file detected: %s", filename)

        try:
            utils.set_hash(full_path, utils.FileStatus.ARRIVED)
        except Exception:
            logging.exception("Failed to insert DB record for '%s'", filename)
            continue

        email_sent = False
        try:
            email_sent = utils.send_email(full_path)
        except Exception:
            logging.exception("Failed to send email for '%s'", filename)

        if email_sent:
            try:
                updated = utils.update_status(file_hash, utils.FileStatus.SENT)
                if not updated:
                    logging.warning(
                        "Failed to update status to SENT for '%s' (hash=%s)",
                        filename,
                        file_hash,
                    )
            except Exception:
                logging.exception("Failed to update status for '%s'", filename)
        else:
            logging.warning(
                "Email send failed, keeping status ARRIVED for '%s'", filename
            )


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    logging.info("Starting cdr_notify")

    database.init_db()
    process_cdr_folder()

    logging.info("cdr_notify finished")


if __name__ == "__main__":
    main()
