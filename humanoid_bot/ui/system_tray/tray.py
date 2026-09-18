"""System tray icon with the assistant menu."""

from __future__ import annotations

from PySide6.QtGui import QAction, QColor, QIcon, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def _make_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    from PySide6.QtGui import QPainter, QPen

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(90, 160, 255))
    painter.setPen(QPen(QColor(20, 24, 34), 4))
    painter.drawEllipse(12, 6, 40, 40)          # head
    painter.drawRoundedRect(10, 44, 44, 18, 9, 9)  # shoulders
    painter.end()
    return QIcon(pixmap)


class SystemTray(QSystemTrayIcon):
    def __init__(self, parent: object | None = None) -> None:
        super().__init__(_make_icon())
        self.setToolTip("Humanoid Bot Assistant")

        menu = QMenu()
        self.action_open = QAction("Open Assistant", menu)
        self.action_voice = QAction("Voice Mode", menu)
        self.action_pause = QAction("Pause Assistant", menu)
        self.action_pause.setCheckable(True)
        self.action_settings = QAction("Settings", menu)
        self.action_logs = QAction("View Logs", menu)
        self.action_exit = QAction("Exit", menu)
        for action in (
            self.action_open,
            self.action_voice,
            self.action_pause,
            self.action_settings,
            self.action_logs,
        ):
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction(self.action_exit)

        self.setContextMenu(menu)

    @property
    def paused(self) -> bool:
        return self.action_pause.isChecked()
