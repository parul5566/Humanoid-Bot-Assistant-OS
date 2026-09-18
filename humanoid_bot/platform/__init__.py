"""Platform abstraction: real backends on Windows, fakes elsewhere.

Windows-specific modules (pywinauto, winsdk, registry autostart) are only
imported inside windows_backend functions so the app runs on any OS.
"""

from __future__ import annotations

import sys
from typing import Any, Protocol


def _import_winreg() -> Any:
    """Import winreg lazily; only available on Windows."""
    import winreg

    return winreg


class PlatformBackend(Protocol):
    """Capabilities that differ per OS."""

    def open_url(self, url: str) -> None: ...
    def open_folder(self, path: str) -> None: ...
    def reveal_in_shell(self, path: str) -> None: ...
    def set_autostart(self, enabled: bool) -> None: ...
    def autostart_enabled(self) -> bool: ...


class LinuxBackend:
    """Non-Windows fallback used in dev/CI. Opens URLs/folders via xdg-open."""

    def open_url(self, url: str) -> None:
        import webbrowser

        webbrowser.open(url)

    def open_folder(self, path: str) -> None:
        import subprocess

        subprocess.Popen(["xdg-open", path])

    def reveal_in_shell(self, path: str) -> None:
        self.open_folder(path)

    def set_autostart(self, enabled: bool) -> None:
        # Desktop autostart is not meaningful in the dev container.
        return None

    def autostart_enabled(self) -> bool:
        return False


class WindowsBackend:
    """Windows 11 implementation. Heavy imports are lazy."""

    def open_url(self, url: str) -> None:
        import webbrowser

        webbrowser.open(url)

    def open_folder(self, path: str) -> None:
        import subprocess

        subprocess.Popen(["explorer", path])

    def reveal_in_shell(self, path: str) -> None:
        import subprocess

        subprocess.Popen(["explorer", "/select,", path])

    def set_autostart(self, enabled: bool) -> None:
        import contextlib

        winreg: Any = _import_winreg()
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, "HumanoidBot", 0, winreg.REG_SZ, sys.executable)
            else:
                with contextlib.suppress(FileNotFoundError):
                    winreg.DeleteValue(key, "HumanoidBot")

    def autostart_enabled(self) -> bool:
        winreg: Any = _import_winreg()
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ
            ) as key:
                winreg.QueryValueEx(key, "HumanoidBot")
                return True
        except (FileNotFoundError, OSError):
            return False


def get_backend() -> PlatformBackend:
    if sys.platform == "win32":
        return WindowsBackend()
    return LinuxBackend()
