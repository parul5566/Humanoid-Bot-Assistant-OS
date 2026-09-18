"""UI tests run with Qt in offscreen mode."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from humanoid_bot.ui.avatar.avatar_state import (  # noqa: E402
    STATE_CAPTIONS,
    AvatarState,
    AvatarStateMachine,
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app  # type: ignore[return-value]


# --- Avatar state machine (pure logic, no Qt needed) -------------------


def test_initial_state_is_idle() -> None:
    machine = AvatarStateMachine()
    assert machine.state is AvatarState.IDLE
    assert machine.caption == "How can I help?"


def test_legal_transitions_notify_observers() -> None:
    machine = AvatarStateMachine()
    seen: list[AvatarState] = []
    machine.observe(seen.append)
    machine.set_state(AvatarState.LISTENING)
    machine.set_state(AvatarState.THINKING)
    machine.set_state(AvatarState.SPEAKING)
    machine.set_state(AvatarState.IDLE)
    assert seen == [
        AvatarState.LISTENING,
        AvatarState.THINKING,
        AvatarState.SPEAKING,
        AvatarState.IDLE,
    ]


def test_every_state_has_a_caption() -> None:
    for state in AvatarState:
        assert STATE_CAPTIONS[state]


def test_error_state_reachable_from_anywhere() -> None:
    machine = AvatarStateMachine()
    machine.set_state(AvatarState.WORKING)
    machine.set_state(AvatarState.IDLE)
    machine.set_state(AvatarState.ERROR)
    assert machine.caption == "Something went wrong."
    machine.set_state(AvatarState.IDLE)  # recovery
    assert machine.state is AvatarState.IDLE


# --- Widgets (offscreen Qt) --------------------------------------------


def test_main_window_builds_and_theme_switches(qapp: QApplication) -> None:
    from humanoid_bot.ui.main_window import MainWindow

    window = MainWindow()
    assert window.avatar.state() is AvatarState.IDLE
    window.apply_theme("light")
    window.apply_theme("dark")
    window.set_avatar(AvatarState.LISTENING)
    assert window.avatar_machine.state is AvatarState.LISTENING


def test_chat_panel_adds_messages(qapp: QApplication) -> None:
    from humanoid_bot.ui.chat.chat_panel import ChatPanel

    panel = ChatPanel()
    panel.add_user_message("hello")
    panel.add_bot_message("hi there")
    assert panel._messages.count() >= 3  # two bubbles + stretch


def test_chat_submit_emits_signal(qapp: QApplication) -> None:
    from humanoid_bot.ui.chat.chat_panel import ChatPanel

    panel = ChatPanel()
    received: list[str] = []
    panel.message_submitted.connect(received.append)
    panel._input.setText("open notepad")
    panel._submit()
    assert received == ["open notepad"]
    assert panel._input.text() == ""


def test_tray_builds_with_all_actions(qapp: QApplication) -> None:
    from humanoid_bot.ui.system_tray.tray import SystemTray

    tray = SystemTray()
    assert tray.action_open.text() == "Open Assistant"
    assert tray.action_voice.text() == "Voice Mode"
    assert tray.action_pause.text() == "Pause Assistant"
    assert tray.action_pause.isCheckable()
    assert tray.action_settings.text() == "Settings"
    assert tray.action_logs.text() == "View Logs"
    assert tray.action_exit.text() == "Exit"
    assert tray.paused is False
