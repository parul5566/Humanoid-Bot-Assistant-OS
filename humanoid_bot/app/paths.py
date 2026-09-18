"""Paths and application constants shared across the app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "HumanoidBot"
ORG_NAME = "HumanoidBot"


def app_data_dir() -> Path:
    """Return the per-user application data directory (created on demand).

    Windows: %APPDATA%/HumanoidBot
    Linux/others: ~/.local/share/HumanoidBot
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return app_data_dir() / "humanoid_bot.db"


def log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path
