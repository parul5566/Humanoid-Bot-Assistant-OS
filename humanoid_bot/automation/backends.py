"""Windows automation backends with a fake for dev/CI.

RealBackend (Windows): subprocess/pywinauto/pyautogui - imported lazily.
FakeBackend: records every operation; used in tests and on Linux.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from humanoid_bot.automation.windows_info import WindowInfo


@dataclass
class FakeBackend:
    """Records operations and simulates windows. Safe everywhere."""

    launched: list[tuple[str, list[str]]] = field(default_factory=list)
    closed: list[str] = field(default_factory=list)
    typed: list[str] = field(default_factory=list)
    keys: list[str] = field(default_factory=list)
    hotkeys: list[list[str]] = field(default_factory=list)
    clicks: list[tuple[int, int, str]] = field(default_factory=list)
    moves: list[tuple[int, int]] = field(default_factory=list)
    simulated_windows: list[WindowInfo] = field(
        default_factory=lambda: [WindowInfo(title="Untitled - Notepad", app_name="notepad")]
    )
    fail_close_for: list[str] = field(default_factory=list)
    read_results: dict[str, str] = field(default_factory=dict)

    # -- operations ----------------------------------------------------
    def launch(self, exe: str, args: list[str]) -> None:
        self.launched.append((exe, args))

    def close_app(self, app: str) -> bool:
        self.closed.append(app)
        return app not in self.fail_close_for

    def type_text(self, text: str) -> None:
        self.typed.append(text)

    def press_key(self, key: str) -> None:
        self.keys.append(key)

    def hotkey(self, keys: list[str]) -> None:
        self.hotkeys.append(keys)

    def click(self, x: int, y: int, button: str = "left") -> None:
        self.clicks.append((x, y, button))

    def move_mouse(self, x: int, y: int) -> None:
        self.moves.append((x, y))

    def find_windows(self, query: str = "") -> list[WindowInfo]:
        q = query.lower()
        return [
            w for w in self.simulated_windows
            if not q or q in w.title.lower() or q in w.app_name.lower()
        ]

    def active_window(self) -> WindowInfo:
        return self.simulated_windows[0]

    def read_window(self, title: str) -> str:
        return self.read_results.get(title, "")


class RealBackend:
    """Windows implementation using subprocess + pywinauto/pyautogui."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("RealBackend is only available on Windows")

    def launch(self, exe: str, args: list[str]) -> None:
        import subprocess

        if exe.endswith(":") or exe.startswith(("http://", "https://")):
            import webbrowser

            webbrowser.open(exe)
            return
        subprocess.Popen([exe, *args], shell=False)

    def close_app(self, app: str) -> bool:
        try:
            import pywinauto  # type: ignore[import-not-found]

            closed = False
            for window in pywinauto.Desktop(backend="uia").windows():
                if app.lower() in (window.window_text() or "").lower():
                    window.close()
                    closed = True
            return closed
        except Exception:
            return False

    def find_windows(self, query: str = "") -> list[WindowInfo]:
        import pywinauto

        q = query.lower()
        results: list[WindowInfo] = []
        for window in pywinauto.Desktop(backend="uia").windows():
            title = window.window_text() or ""
            if not q or q in title.lower():
                results.append(WindowInfo(title=title, app_name=title.split(" - ")[-1]))
        return results

    def active_window(self) -> WindowInfo:
        from pywinauto import Desktop

        window = Desktop(backend="uia").top_window()
        title = window.window_text() or ""
        return WindowInfo(title=title, app_name=title.split(" - ")[-1])

    def read_window(self, title: str) -> str:
        import pywinauto

        for window in pywinauto.Desktop(backend="uia").windows():
            if title.lower() in (window.window_text() or "").lower():
                return str(window.window_text())
        return ""

    def type_text(self, text: str) -> None:
        import pyautogui  # type: ignore[import-untyped]

        pyautogui.typewrite(text, interval=0.01)

    def press_key(self, key: str) -> None:
        import pyautogui

        pyautogui.press(key)

    def hotkey(self, keys: list[str]) -> None:
        import pyautogui

        pyautogui.hotkey(*keys)

    def click(self, x: int, y: int, button: str = "left") -> None:
        import pyautogui

        pyautogui.click(x=x, y=y, button=button)

    def move_mouse(self, x: int, y: int) -> None:
        import pyautogui

        pyautogui.moveTo(x, y)


def get_backend() -> FakeBackend | RealBackend:
    if sys.platform == "win32":
        return RealBackend()
    return FakeBackend()
