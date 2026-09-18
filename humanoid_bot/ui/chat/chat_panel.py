"""Chat panel: message list + input bar with mic button."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


def _bubble(text: str, from_user: bool) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    color = "#2f5f8f" if from_user else "#33384a"
    label.setStyleSheet(
        f"background: {color}; color: #f2f4f8; border-radius: 12px;"
        "padding: 8px 12px; margin: 3px 0;"
    )
    label.setMaximumWidth(520)
    return label


class ChatPanel(QWidget):
    """Conversation view. Emits message_submitted(text) for user input."""

    message_submitted = Signal(str)
    mic_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll_widget = QWidget()
        self._messages = QVBoxLayout(self._scroll_widget)
        self._messages.addStretch(1)
        self._scroll.setWidget(self._scroll_widget)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(self._scroll, 1)

        input_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask anything...")
        self._input.returnPressed.connect(self._submit)
        input_row.addWidget(self._input, 1)

        self._mic = QPushButton("🎙")
        self._mic.setToolTip("Push to talk (Ctrl+Shift+V)")
        self._mic.setFixedWidth(44)
        self._mic.clicked.connect(self.mic_clicked.emit)
        input_row.addWidget(self._mic)

        layout.addLayout(input_row)

    # ------------------------------------------------------------------
    def _submit(self) -> None:
        text = self._input.text().strip()
        if text:
            self._input.clear()
            self.add_user_message(text)
            self.message_submitted.emit(text)

    def add_user_message(self, text: str) -> None:
        self._messages.insertWidget(self._messages.count() - 1, _bubble(text, True))
        self._scroll_to_bottom()

    def add_bot_message(self, text: str) -> None:
        self._messages.insertWidget(self._messages.count() - 1, _bubble(text, False))
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())
