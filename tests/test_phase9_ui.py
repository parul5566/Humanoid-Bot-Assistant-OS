import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from humanoid_bot.app.config import AppConfig
from humanoid_bot.security.permissions import PermissionManager
from humanoid_bot.storage.database import Database


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])  # type: ignore[return-value]


def test_history_panel_lists_repeat_delete(qapp, monkeypatch) -> None:
    from humanoid_bot.ui.history import HistoryPanel

    db = Database.open(":memory:")
    db.add_task("Opened VS Code")
    db.add_task("Created Project folder")
    repeated: list[str] = []
    panel = HistoryPanel(db, on_repeat=repeated.append)
    assert panel.list.count() == 2

    panel.list.setCurrentRow(1)  # newest first: row 1 is the older task
    panel._repeat_selected()
    assert repeated == ["Opened VS Code"]

    panel._delete_selected()
    assert panel.list.count() == 1


def test_system_monitor_updates(qapp) -> None:
    from humanoid_bot.ui.system_monitor import SystemMonitorPanel

    panel = SystemMonitorPanel(refresh_ms=60000)
    panel.refresh()
    assert panel.labels["cpu"].text().endswith("%")
    assert panel.labels["network"].text() in ("Connected", "Disconnected")


def test_settings_dialog_applies_privacy(qapp) -> None:
    from humanoid_bot.ui.settings.settings_dialog import SettingsDialog

    db = Database.open(":memory:")
    config = AppConfig()
    permissions = PermissionManager(config.privacy, db)
    dialog = SettingsDialog(config, permissions)
    dialog.allow_screen.setChecked(True)
    dialog.theme.setCurrentText("light")
    dialog.provider.setCurrentText("ollama")
    dialog._apply()
    assert permissions.privacy.allow_screen_access is True
    assert config.general.theme == "light"
    assert config.ai.provider == "ollama"

    reloaded = PermissionManager.load(db)
    assert reloaded.privacy.allow_screen_access is True


def test_settings_dialog_cancel_keeps_values(qapp) -> None:
    from humanoid_bot.ui.settings.settings_dialog import SettingsDialog

    config = AppConfig()
    permissions = PermissionManager(config.privacy)
    dialog = SettingsDialog(config, permissions)
    dialog.allow_screen.setChecked(True)
    dialog.reject()
    assert permissions.privacy.allow_screen_access is False
