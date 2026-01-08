# cdr_notify.py

import logging

import utils
from utils import ConfigError


def main() -> None:
    """Main entry point for CDR notification service"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        # Load and validate configuration
        config = utils.load_config()
        utils.validate_config(config)

        # Initialize database
        utils.init_database(config)

        # Get new files to process
        new_files = utils.get_new_files(config)
        if not new_files:
            logging.info("No new CDR files found")
            return

        logging.info(f"Found {len(new_files)} new file(s) to process")

        # Process each new file
        for file_path in new_files:
            utils.process_file(file_path, config)

    except ConfigError as e:
        logging.error(f"Configuration error: {e}")
        exit(1)
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
