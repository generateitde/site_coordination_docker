"""SQLite backup upload via Power Automate HTTP trigger."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import requests

from .config import DB_BACKUP_FLOW_URL, load_db_backup_flow_secret


def upload_sqlite_backup_via_flow(
    db_path: str | Path,
    remote_filename: Optional[str] = None,
    timeout: int = 30,
) -> None:
    """Upload a SQLite backup via the Power Automate flow."""
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"SQLite database not found at {path}.")
    token = load_db_backup_flow_secret()
    filename = remote_filename or path.name
    content = base64.b64encode(path.read_bytes()).decode("utf-8")
    payload = {"token": token, "filename": filename, "content": content}
    response = requests.post(DB_BACKUP_FLOW_URL, json=payload, timeout=timeout)
    if response.status_code not in {200, 202}:
        raise RuntimeError(
            "DB backup flow failed with status "
            f"{response.status_code}: {response.text}"
        )
