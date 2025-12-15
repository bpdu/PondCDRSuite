import logging
import os
import smtplib
from email.message import EmailMessage


CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "config",
    "config.txt",
)

RESOURCES_PATH = os.path.join(
    os.path.dirname(__file__),
    "resources",
)


def _load_config() -> dict[str, str]:
    config: dict[str, str] = {}

    if not os.path.isfile(CONFIG_PATH):
        raise RuntimeError(f"Config file not found: {CONFIG_PATH}")

    with open(CONFIG_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()

    return config


def _load_template(filename: str) -> str:
    path = os.path.join(RESOURCES_PATH, filename)
    if not os.path.isfile(path):
        raise RuntimeError(f"Template not found: {path}")

    with open(path) as f:
        return f.read()


def send_email(filepath: str) -> bool:
    try:
        config = _load_config()

        smtp_host = config["SMTP_HOST"]
        smtp_port = int(config.get("SMTP_PORT", 587))
        email_from = config["EMAIL_FROM"]
        email_to = config["EMAIL_TO"]

        filename = os.path.basename(filepath)

        subject_template = _load_template("email_subject.txt")
        body_template = _load_template("email_body.txt")

        subject = subject_template.format(filename=filename)
        body = body_template.format(filename=filename)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = email_to
        msg.set_content(body)

        with open(filepath, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="text",
                subtype="plain",
                filename=filename,
            )

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.send_message(msg)

        return True

    except Exception:
        logging.exception("Failed to send email for %s", filepath)
        return False
