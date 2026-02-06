"""SharePoint backup synchronization for the coordination app."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import threading
import time
from typing import Optional

import requests

from site_coordination.config import load_database_config, load_env


@dataclass(frozen=True)
class SharePointConfig:
    """Configuration required to upload backups to SharePoint."""

    tenant_id: str
    client_id: str
    client_secret: str
    site_id: str
    drive_id: str
    remote_path: str
    interval_seconds: int = 300


def _parse_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_sharepoint_config() -> Optional[SharePointConfig]:
    """Load SharePoint configuration from environment variables."""

    load_env()
    if not _parse_enabled(os.environ.get("SITE_COORDINATION_SHAREPOINT_ENABLED", "")):
        return None

    tenant_id = os.environ.get("SITE_COORDINATION_SHAREPOINT_TENANT_ID", "").strip()
    client_id = os.environ.get("SITE_COORDINATION_SHAREPOINT_CLIENT_ID", "").strip()
    client_secret = os.environ.get(
        "SITE_COORDINATION_SHAREPOINT_CLIENT_SECRET", ""
    ).strip()
    site_id = os.environ.get("SITE_COORDINATION_SHAREPOINT_SITE_ID", "").strip()
    drive_id = os.environ.get("SITE_COORDINATION_SHAREPOINT_DRIVE_ID", "").strip()
    remote_path = os.environ.get(
        "SITE_COORDINATION_SHAREPOINT_REMOTE_PATH",
        "backups/site_coordination.sqlite",
    ).strip()
    interval_raw = os.environ.get("SITE_COORDINATION_SHAREPOINT_INTERVAL_SECONDS", "300")

    if not all([tenant_id, client_id, client_secret, site_id, drive_id, remote_path]):
        return None

    try:
        interval_seconds = max(int(interval_raw), 60)
    except ValueError:
        interval_seconds = 300

    return SharePointConfig(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        site_id=site_id,
        drive_id=drive_id,
        remote_path=remote_path.lstrip("/"),
        interval_seconds=interval_seconds,
    )


class SharePointSync:
    """Background loop that uploads the database to SharePoint."""

    def __init__(
        self,
        config: SharePointConfig,
        database_path: Path,
        logger: logging.Logger,
    ) -> None:
        self._config = config
        self._database_path = database_path
        self._logger = logger
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._sync_once()
            self._stop_event.wait(self._config.interval_seconds)

    def _sync_once(self) -> None:
        if not self._database_path.exists():
            self._logger.warning(
                "SharePoint sync skipped; database not found at %s",
                self._database_path,
            )
            return
        try:
            token = _request_access_token(self._config)
            _upload_database(self._config, self._database_path, token)
            self._logger.info("SharePoint backup uploaded to %s", self._config.remote_path)
        except Exception as exc:  # noqa: BLE001 - log and continue
            self._logger.warning("SharePoint sync failed: %s", exc)


def _request_access_token(config: SharePointConfig) -> str:
    token_url = (
        "https://login.microsoftonline.com/"
        f"{config.tenant_id}/oauth2/v2.0/token"
    )
    response = requests.post(
        token_url,
        data={
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("SharePoint token missing from response")
    return token


def _upload_database(
    config: SharePointConfig,
    database_path: Path,
    token: str,
) -> None:
    upload_url = (
        "https://graph.microsoft.com/v1.0/sites/"
        f"{config.site_id}/drives/{config.drive_id}/root:/"
        f"{config.remote_path}:/content"
    )
    with database_path.open("rb") as handle:
        response = requests.put(
            upload_url,
            headers={"Authorization": f"Bearer {token}"},
            data=handle,
            timeout=60,
        )
    response.raise_for_status()


def start_sharepoint_sync(logger: logging.Logger) -> Optional[SharePointSync]:
    """Start SharePoint sync if enabled and configured."""

    config = load_sharepoint_config()
    if not config:
        logger.info("SharePoint sync disabled or not configured.")
        return None
    database_path = load_database_config().path
    syncer = SharePointSync(config=config, database_path=database_path, logger=logger)
    syncer.start()
    return syncer
