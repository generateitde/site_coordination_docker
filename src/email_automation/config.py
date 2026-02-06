"""Configuration for Power Automate email automation."""

from __future__ import annotations

from dataclasses import dataclass

from flow_automation.config import EMAIL_FLOW_URL, load_email_flow_secret


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Power Automate integration."""

    flow_secret: str


def load_settings() -> Settings:
    """Load settings from the local .env file."""
    return Settings(flow_secret=load_email_flow_secret())


FLOW_URL = EMAIL_FLOW_URL
