import logging
import os

import database
import email_sender
import telegram_sender
import utils


def _is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = utils.load_config()

    cdr_folder = config.get("CDR_FOLDER", "").strip()
    if not cdr_folder:
        raise RuntimeError("CDR_FOLDER is not set in config/config.txt")

    db_name = config.get("DB_NAME", "").strip()
    if db_name:
        os.environ["DB_NAME"] = db_name

    database.init_db()
    logging.info("Starting CDR notify service")

    files = utils.get_files(cdr_folder)
    found_new_files = False

    email_enabled = _is_true(config.get("EMAIL_SEND", ""))
    telegram_enabled = _is_true(config.get("TELEGRAM_SEND", ""))

    for full_path in files:
        if utils.is_known_file(full_path):
            continue

        found_new_files = True

        file_hash = utils.calculate_hash(full_path)
        if not file_hash:
            utils.insert_file_record(full_path, "", utils.FileStatus.FAILED, "Hash calculation failed")
            continue

        utils.insert_file_record(full_path, file_hash, utils.FileStatus.ARRIVED, "")

        email_send_status = False
        telegram_send_status = False
        errors: list[str] = []

        if telegram_enabled:
            try:
                telegram_send_status = telegram_sender.send_message(full_path)
                if not telegram_send_status:
                    errors.append("Telegram send returned False")
            except Exception as e:
                errors.append(f"Telegram error: {utils.safe_error(e)}")

        if email_enabled:
            try:
                email_send_status = email_sender.send_email(full_path)
                if not email_send_status:
                    errors.append("Email send returned False")
            except Exception as e:
                errors.append(f"Email error: {utils.safe_error(e)}")

        if email_send_status or telegram_send_status:
            utils.update_file_status(full_path, utils.FileStatus.SENT, "")
            logging.info(
                "File processed successfully: %s (email=%s telegram=%s)",
                utils.get_filename(full_path),
                email_send_status,
                telegram_send_status,
            )
        else:
            if email_enabled or telegram_enabled:
                utils.update_file_status(full_path, utils.FileStatus.FAILED, "; ".join(errors))
                logging.info(
                    "File processed with failure: %s (email=%s telegram=%s)",
                    utils.get_filename(full_path),
                    email_send_status,
                    telegram_send_status,
                )
            else:
                utils.update_file_status(full_path, utils.FileStatus.SKIPPED, "Notifications disabled")
                logging.info(
                    "File processed with notifications disabled: %s",
                    utils.get_filename(full_path),
                )

    if not found_new_files:
        logging.info("No new CDR files found")


if __name__ == "__main__":
    main()
