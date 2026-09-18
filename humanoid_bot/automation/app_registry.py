"""Application registry: known apps with launch methods, user-extensible."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class AppEntry(BaseModel):
    name: str                       # canonical name ("notepad")
    display: str                    # human name ("Notepad")
    executable: str                 # exe or command
    args: list[str] = Field(default_factory=list)
    launch_method: str = "shell"    # shell | uwp | custom
    aliases: list[str] = Field(default_factory=list)


class AppRegistry:
    """Resolves app names/aliases to launch entries.

    Ships with defaults for Windows 11; user entries (loaded from
    config.json via AppConfig in a later phase) override/extend them.
    """

    def __init__(self, apps: list[AppEntry] | None = None) -> None:
        self._apps: dict[str, AppEntry] = {}
        for app in apps or self._defaults():
            self.add(app)

    def add(self, app: AppEntry) -> None:
        self._apps[app.name.lower()] = app

    def remove(self, name: str) -> bool:
        return self._apps.pop(name.lower(), None) is not None

    def resolve(self, query: str) -> AppEntry | None:
        """Match by name or alias, case-insensitive."""
        q = query.strip().lower()
        if q in self._apps:
            return self._apps[q]
        for app in self._apps.values():
            if q in (a.lower() for a in app.aliases):
                return app
        return None

    def all_names(self) -> list[str]:
        return sorted(self._apps)

    # ------------------------------------------------------------------
    @staticmethod
    def _defaults() -> list[AppEntry]:
        code = "code"
        if Path("C:/Users").exists():  # pragma: no cover - windows only
            pass
        return [
            AppEntry(name="notepad", display="Notepad", executable="notepad.exe"),
            AppEntry(name="calculator", display="Calculator", executable="calc.exe",
                     aliases=["calc"]),
            AppEntry(name="chrome", display="Google Chrome", executable="chrome.exe",
                     aliases=["google chrome", "browser"]),
            AppEntry(name="edge", display="Microsoft Edge", executable="msedge.exe"),
            AppEntry(name="code", display="Visual Studio Code", executable=code,
                     aliases=["vscode", "vs code", "visual studio code"]),
            AppEntry(name="explorer", display="File Explorer", executable="explorer.exe",
                     aliases=["files", "file explorer"]),
            AppEntry(name="taskmanager", display="Task Manager",
                     executable="taskmgr.exe", aliases=["task manager"]),
            AppEntry(name="terminal", display="Windows Terminal", executable="wt.exe",
                     aliases=["windows terminal", "console"]),
            AppEntry(name="paint", display="Paint", executable="mspaint.exe"),
            AppEntry(name="settings", display="Windows Settings",
                     executable="ms-settings:", launch_method="shell",
                     aliases=["windows settings"]),
        ]
