"""Configuration helpers for Power Automate flows."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

EMAIL_FLOW_URL = "https://prod-...logic.azure.com/..."  # hier eintragen
DB_BACKUP_FLOW_URL = "https://prod-...logic.azure.com/..."  # hier eintragen


def _load_env() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    load_dotenv(env_path)


def load_email_flow_secret() -> str:
    """Return the email flow secret from .env."""
    _load_env()
    secret = os.environ.get("EMAIL_FLOW_SECRET", "").strip()
    if not secret:
        raise RuntimeError(
            "EMAIL_FLOW_SECRET is missing. Set it in the .env file "
            "(see .env.example)."
        )
    return secret


def load_db_backup_flow_secret() -> str:
    """Return the DB backup flow secret from .env."""
    _load_env()
    secret = os.environ.get("DB_BACKUP_FLOW_SECRET", "").strip()
    if not secret:
        raise RuntimeError(
            "DB_BACKUP_FLOW_SECRET is missing. Set it in the .env file "
            "(see .env.example)."
        )
    return secret
