"""Main window: avatar + chat, dark/light Fluent-inspired theme, shortcuts."""

from __future__ import annotations

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from humanoid_bot.ui.avatar.avatar_state import AvatarState, AvatarStateMachine
from humanoid_bot.ui.avatar.avatar_widget import AvatarWidget
from humanoid_bot.ui.chat.chat_panel import ChatPanel

_DARK = """
QMainWindow, QWidget { background: #1b1e27; color: #f2f4f8; }
QLineEdit { background: #262a38; border: 1px solid #3a4054; border-radius: 10px;
            padding: 8px; color: #f2f4f8; }
QPushButton { background: #262a38; border: 1px solid #3a4054; border-radius: 10px;
              padding: 8px; color: #f2f4f8; }
QPushButton:hover { background: #303650; }
QMenu { background: #262a38; color: #f2f4f8; border: 1px solid #3a4054; }
"""

_LIGHT = """
QMainWindow, QWidget { background: #f3f4f8; color: #1b1e27; }
QLineEdit { background: #ffffff; border: 1px solid #d5d9e2; border-radius: 10px;
            padding: 8px; }
QPushButton { background: #ffffff; border: 1px solid #d5d9e2; border-radius: 10px;
              padding: 8px; }
QPushButton:hover { background: #e8ecf5; }
QMenu { background: #ffffff; border: 1px solid #d5d9e2; }
"""


class MainWindow(QMainWindow):
    """Top-level window: avatar panel + chat panel, with global shortcuts."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Humanoid Bot Assistant")
        self.resize(760, 640)

        self.avatar_machine = AvatarStateMachine()

        self.avatar = AvatarWidget()
        self.chat = ChatPanel()
        self.chat.message_submitted.connect(self._on_user_message)

        self.avatar_frame = QFrame()
        self.avatar_frame.setStyleSheet(
            "QFrame { background: rgba(255,255,255,0.03); border-radius: 16px; }"
        )
        avatar_layout = QHBoxLayout(self.avatar_frame)
        avatar_layout.addWidget(self.avatar)

        self._stack = QStackedWidget()
        self._stack.addWidget(self.chat)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(self.avatar_frame, 2)
        layout.addWidget(self._stack, 3)
        self.setCentralWidget(central)

        self.apply_theme("dark")

        # Shortcuts (configurable defaults).
        self._shortcut_activate = QShortcut(QKeySequence("Ctrl+Space"), self)
        self._shortcut_activate.activated.connect(self.activate_assistant)
        self._shortcut_voice = QShortcut(QKeySequence("Ctrl+Shift+V"), self)
        self._shortcut_voice.activated.connect(self.activate_voice_mode)
        self._shortcut_open = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        self._shortcut_open.activated.connect(self.activate_assistant)

        self.avatar_machine.observe(self._on_avatar_state)

    # ------------------------------------------------------------------
    def apply_theme(self, theme: str) -> None:
        if theme == "light":
            self.setStyleSheet(_LIGHT)
        else:
            self.setStyleSheet(_DARK)

    def activate_assistant(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.chat._input.setFocus()

    def activate_voice_mode(self) -> None:
        self.activate_assistant()
        self.set_avatar(AvatarState.LISTENING)
        # Phase 3 wires real audio capture to this state.

    # ------------------------------------------------------------------
    def set_avatar(self, state: AvatarState, caption: str | None = None) -> None:
        self.avatar_machine.set_state(state, caption)

    def _on_avatar_state(self, state: AvatarState) -> None:
        self.avatar.set_state(state)

    def _on_user_message(self, text: str) -> None:
        # Phase 4 connects this to the AI orchestrator; for now acknowledge.
        self.set_avatar(AvatarState.THINKING)
        self.chat.add_bot_message(f"Received: {text}")
        self.set_avatar(AvatarState.IDLE)
