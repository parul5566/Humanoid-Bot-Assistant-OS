"""Application entry point and lifecycle management."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from humanoid_bot.app.config import AppConfig
from humanoid_bot.logging_setup import setup_logging
from humanoid_bot.storage.database import Database


class AppLifecycle:
    """Owns the long-lived singletons (config, database) and clean shutdown."""

    def __init__(self) -> None:
        self.config: AppConfig = AppConfig.load()
        self.database: Database = Database.open()

    def shutdown(self) -> None:
        self.config.save()


def create_app(lifecycle: AppLifecycle) -> QApplication:
    """Build the QApplication, main window and tray. Returns the app to exec."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    assert isinstance(app, QApplication)

    from humanoid_bot.ui.main_window import MainWindow
    from humanoid_bot.ui.system_tray.tray import SystemTray

    window = MainWindow()
    window.apply_theme(lifecycle.config.general.theme)

    tray = SystemTray()
    tray.action_open.triggered.connect(window.activate_assistant)
    tray.action_voice.triggered.connect(window.activate_voice_mode)
    tray.action_exit.triggered.connect(app.quit)
    tray.show()

    app.window = window  # type: ignore[attr-defined]
    app.tray = tray  # type: ignore[attr-defined]
    window.show()
    return app


def main() -> int:
    setup_logging()
    lifecycle = AppLifecycle()
    app = create_app(lifecycle)
    exit_code = app.exec()
    lifecycle.shutdown()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
