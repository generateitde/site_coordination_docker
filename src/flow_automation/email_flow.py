"""Email delivery via Power Automate HTTP trigger."""

from __future__ import annotations

from typing import Mapping

import requests

from .config import EMAIL_FLOW_URL, load_email_flow_secret


def send_email_via_flow(
    to: str,
    subject: str,
    body: str,
    content_type: str = "text",
    timeout: int = 10,
) -> None:
    """Send an email via the Power Automate flow."""
    token = load_email_flow_secret()
    payload: Mapping[str, str] = {
        "token": token,
        "to": to,
        "subject": subject,
        "body": body,
        "contentType": content_type,
    }
    response = requests.post(EMAIL_FLOW_URL, json=payload, timeout=timeout)
    if response.status_code not in {200, 202}:
        raise RuntimeError(
            "Email flow failed with status "
            f"{response.status_code}: {response.text}"
        )
