"""Avatar state machine - pure logic, no Qt dependency."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto


class AvatarState(Enum):
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    WORKING = auto()
    ERROR = auto()


STATE_CAPTIONS: dict[AvatarState, str] = {
    AvatarState.IDLE: "How can I help?",
    AvatarState.LISTENING: "Listening...",
    AvatarState.THINKING: "Thinking...",
    AvatarState.SPEAKING: "Speaking...",
    AvatarState.WORKING: "Working...",
    AvatarState.ERROR: "Something went wrong.",
}

# Any state may enter ERROR (errors can surface anywhere) and ERROR may
# recover to any state. All other transitions are also permitted.
_ALLOWED: dict[AvatarState, set[AvatarState]] = {
    state: set(AvatarState) for state in AvatarState
}

StateCallback = Callable[[AvatarState], None]


class AvatarStateMachine:
    """Tracks the avatar state and notifies observers on change."""

    def __init__(self) -> None:
        self._state = AvatarState.IDLE
        self._observers: list[StateCallback] = []

    @property
    def state(self) -> AvatarState:
        return self._state

    @property
    def caption(self) -> str:
        return STATE_CAPTIONS[self._state]

    def set_state(self, new_state: AvatarState, caption: str | None = None) -> None:
        if new_state not in _ALLOWED[self._state]:
            raise ValueError(f"Illegal avatar transition {self._state} -> {new_state}")
        self._state = new_state
        for cb in list(self._observers):
            cb(self._state)

    def observe(self, callback: StateCallback) -> None:
        self._observers.append(callback)
