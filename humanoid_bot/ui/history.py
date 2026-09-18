"""Task history panel: today's actions with repeat/delete."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from humanoid_bot.storage.database import Database


class HistoryPanel(QWidget):

    def __init__(self, database: Database, on_repeat: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self.db = database
        self.on_repeat = on_repeat or (lambda _summary: None)

        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        buttons = QHBoxLayout()
        repeat_btn = QPushButton("Repeat")
        repeat_btn.clicked.connect(self._repeat_selected)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        buttons.addWidget(repeat_btn)
        buttons.addWidget(delete_btn)
        buttons.addStretch(1)
        buttons.addWidget(refresh_btn)
        layout.addLayout(buttons)

        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for task in self.db.recent_tasks(100):
            time_str = task.created_at.strftime("%H:%M")
            item = QListWidgetItem(f"{time_str}  {task.summary}")
            item.setData(0x0100, task.id)  # UserRole
            self.list.addItem(item)

    def _selected_task_id(self) -> int | None:
        item = self.list.currentItem()
        raw = None if item is None else item.data(0x0100)
        if raw is None:
            return None
        return int(raw)

    def _repeat_selected(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        for task in self.db.recent_tasks(100):
            if task.id == task_id:
                self.on_repeat(task.summary)
                return

    def _delete_selected(self) -> None:
        task_id = self._selected_task_id()
        if task_id is not None:
            self.db.delete_task(task_id)
            self.refresh()
