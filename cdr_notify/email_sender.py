from __future__ import annotations

import base64
import logging

import requests

import utils


def _get_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    response = requests.post(
        url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def send_email(
    full_path: str, notification: dict[str, str], config: dict[str, str]
) -> bool:
    try:
        tenant_id = config.get("MS_TENANT_ID", "").strip()
        client_id = config.get("MS_CLIENT_ID", "").strip()
        client_secret = config.get("MS_CLIENT_SECRET", "").strip()
        email_from = config.get("EMAIL_FROM", "").strip()
        recipients = [
            addr.strip() for addr in config.get("EMAIL_TO", "").split(",")
            if addr.strip()
        ]

        if not tenant_id:
            raise RuntimeError("MS_TENANT_ID is not set in msgraph.env")
        if not client_id:
            raise RuntimeError("MS_CLIENT_ID is not set in msgraph.env")
        if not client_secret:
            raise RuntimeError("MS_CLIENT_SECRET is not set in msgraph.env")
        if not email_from:
            raise RuntimeError(f"EMAIL_FROM is not set in {utils.CONFIG_PATH}")
        if not recipients:
            raise RuntimeError(f"EMAIL_TO is not set in {utils.CONFIG_PATH}")

        access_token = _get_access_token(tenant_id, client_id, client_secret)

        with open(full_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "message": {
                "subject": notification["subject"],
                "body": {
                    "contentType": "Text",
                    "content": notification["body"],
                },
                "toRecipients": [
                    {"emailAddress": {"address": addr}} for addr in recipients
                ],
                "attachments": [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": notification["filename"],
                        "contentType": "text/plain",
                        "contentBytes": file_content,
                    }
                ],
            }
        }

        url = f"https://graph.microsoft.com/v1.0/users/{email_from}/sendMail"
        response = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        response.raise_for_status()
        return True

    except Exception:
        logging.exception(
            "Failed to send email for file %s", notification["filename"]
        )
        return False
