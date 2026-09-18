"""Text-to-speech abstraction with interruptible speech.

Backends:
- FakeTTS     - records what it was asked to say; for tests/headless dev
- LocalTTS    - pyttsx3 (SAPI5 on Windows, espeak fallback on Linux)
"""

from __future__ import annotations

import threading
from typing import Protocol


class TextToSpeech(Protocol):
    def speak(self, text: str) -> None: ...
    def stop(self) -> None: ...
    @property
    def speaking(self) -> bool: ...


class FakeTTS:
    """Stores utterances instead of speaking them (interruptible)."""

    def __init__(self) -> None:
        self.utterances: list[str] = []
        self._speaking = False
        self._lock = threading.Lock()

    def speak(self, text: str) -> None:
        with self._lock:
            self._speaking = True
        self.utterances.append(text)
        # No real audio; caller controls stop(). For test determinism we
        # finish immediately unless a test holds the lock.
        with self._lock:
            self._speaking = False

    def stop(self) -> None:
        with self._lock:
            self._speaking = False

    @property
    def speaking(self) -> bool:
        with self._lock:
            return self._speaking


class LocalTTS:
    """pyttsx3-based speech on a worker thread, with barge-in stop."""

    def __init__(self, rate: float = 1.0, voice: str = "") -> None:
        self._rate = rate
        self._voice = voice
        self._lock = threading.Lock()
        self._speaking = False
        self._engine: object | None = None

    def _ensure_engine(self) -> object:
        if self._engine is None:
            try:
                import pyttsx3  # type: ignore[import-not-found]
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "Local TTS requires pyttsx3 (pip install pyttsx3)"
                ) from exc
            engine = pyttsx3.init()
            engine.setProperty("rate", int(180 * self._rate))
            if self._voice:
                engine.setProperty("voice", self._voice)
            self._engine = engine
        return self._engine

    def speak(self, text: str) -> None:
        engine = self._ensure_engine()

        def _run() -> None:
            with self._lock:
                self._speaking = True
            engine.say(text)  # type: ignore[attr-defined]
            engine.runAndWait()  # type: ignore[attr-defined]
            with self._lock:
                self._speaking = False

        threading.Thread(target=_run, daemon=True).start()

    def stop(self) -> None:
        with self._lock:
            engine = self._engine
            self._speaking = False
        if engine is not None:
            engine.stop()  # type: ignore[attr-defined]

    @property
    def speaking(self) -> bool:
        with self._lock:
            return self._speaking


def create_tts(backend: str, **kwargs: float) -> TextToSpeech:
    if backend == "fake":
        return FakeTTS()
    if backend == "local":
        return LocalTTS(rate=float(kwargs.get("rate", 1.0)))
    raise ValueError(f"Unknown TTS backend: {backend}")
