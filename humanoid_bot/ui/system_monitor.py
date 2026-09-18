"""Live system monitor dashboard."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QGridLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from humanoid_bot.tools.system_tools import system_stats

_ROWS = ["cpu", "ram", "disk", "battery", "network"]


class SystemMonitorPanel(QWidget):
    def __init__(self, parent: QWidget | None = None, refresh_ms: int = 2000) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        self.bars: dict[str, QProgressBar] = {}
        self.labels: dict[str, QLabel] = {}

        for row, key in enumerate(_ROWS):
            title = QLabel(key.upper())
            title.setStyleSheet("font-weight: bold;")
            grid.addWidget(title, row, 0)
            bar = QProgressBar()
            bar.setRange(0, 100)
            grid.addWidget(bar, row, 1)
            value = QLabel("-")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.addWidget(value, row, 2)
            self.bars[key] = bar
            self.labels[key] = value

        layout.addLayout(grid)
        layout.addStretch(1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(refresh_ms)
        self.refresh()

    def refresh(self) -> None:
        try:
            stats = system_stats()
        except Exception:
            return
        for key in _ROWS:
            value = stats.get(f"{key}_percent")
            if value is None and key == "battery":
                self.bars[key].setValue(0)
                self.labels[key].setText("n/a")
                continue
            if value is None:
                continue
            self.bars[key].setValue(int(value))
            self.labels[key].setText(f"{value:.0f}%")
        network = "Connected" if stats.get("network_up") else "Disconnected"
        self.bars["network"].setValue(100 if stats.get("network_up") else 0)
        self.labels["network"].setText(network)
