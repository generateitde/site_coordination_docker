"""SharePoint backup synchronization for the coordination app."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import threading
from typing import Optional

from site_coordination.config import load_database_config, load_env
from flow_automation.config import load_db_backup_flow_secret
from flow_automation.sharepoint_backup_flow import upload_sqlite_backup_via_flow


class SharePointConfig:
    """Configuration required to upload backups via Power Automate."""

    def __init__(self, remote_filename: str, interval_seconds: int = 300) -> None:
        self.remote_filename = remote_filename
        self.interval_seconds = interval_seconds


def _parse_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_sharepoint_config() -> Optional[SharePointConfig]:
    """Load backup configuration from environment variables."""

    load_env()
    if not _parse_enabled(os.environ.get("SITE_COORDINATION_SHAREPOINT_ENABLED", "true")):
        return None
    remote_filename = os.environ.get(
        "SITE_COORDINATION_DB_BACKUP_FILENAME", "site_coordination.sqlite"
    ).strip()
    interval_raw = os.environ.get("SITE_COORDINATION_DB_BACKUP_INTERVAL_SECONDS", "300")

    try:
        interval_seconds = max(int(interval_raw), 60)
    except ValueError:
        interval_seconds = 300

    return SharePointConfig(
        remote_filename=remote_filename,
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
            upload_sqlite_backup_via_flow(
                self._database_path, remote_filename=self._config.remote_filename
            )
            self._logger.info(
                "SharePoint backup uploaded via flow as %s",
                self._config.remote_filename,
            )
        except Exception as exc:  # noqa: BLE001 - log and continue
            self._logger.warning("SharePoint sync failed: %s", exc)


def start_sharepoint_sync(logger: logging.Logger) -> Optional[SharePointSync]:
    """Start SharePoint sync if enabled and configured."""

    config = load_sharepoint_config()
    if not config:
        logger.info("SharePoint sync disabled or not configured.")
        return None
    load_db_backup_flow_secret()
    database_path = load_database_config().path
    syncer = SharePointSync(config=config, database_path=database_path, logger=logger)
    syncer.start()
    return syncer
