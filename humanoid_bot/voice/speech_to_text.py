"""Speech-to-text abstraction.

Backends:
- FakeSTT  - deterministic, for tests/headless dev
- CloudSTT - provider-agnostic placeholder posting audio to a configured
             endpoint (wired to the AI provider layer in Phase 4)
- LocalSTT - placeholder for faster-whisper/Vosk; imports lazily so the app
             runs without the optional voice extras installed
"""

from __future__ import annotations

from typing import Protocol


class SpeechToText(Protocol):
    def transcribe(self, audio: bytes, sample_rate: int = 16000) -> str: ...


class FakeSTT:
    """Echoes canned phrases; useful for driving the pipeline in tests."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses = responses or ["open notepad"]
        self._index = 0

    def transcribe(self, audio: bytes, sample_rate: int = 16000) -> str:
        if not self.responses:
            return ""
        phrase = self.responses[self._index % len(self.responses)]
        self._index += 1
        return phrase


class LocalSTT:
    """Local whisper-based transcription (requires the voice extras)."""

    def __init__(self, model: str = "base") -> None:
        self._model_name = model
        self._model: object | None = None

    def _ensure_model(self) -> object:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel  # type: ignore[import-not-found]
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "Local STT requires faster-whisper (pip install faster-whisper)"
                ) from exc
            self._model = WhisperModel(self._model_name, compute_type="int8")
        return self._model

    def transcribe(self, audio: bytes, sample_rate: int = 16000) -> str:
        import io
        import wave

        model = self._ensure_model()
        with wave.open(io.BytesIO(audio), "rb") as wav:
            frames = wav.readframes(wav.getnframes())
        import numpy as np

        samples = np.frombuffer(frames, dtype=np.int16).astype("float32") / 32768.0
        segments, _info = model.transcribe(samples, language="en")  # type: ignore[attr-defined,no-any-return,unused-ignore]
        return " ".join(segment.text.strip() for segment in segments).strip()


class CloudSTT:
    """Sends audio to a cloud STT endpoint (endpoint configured via env)."""

    def __init__(self, endpoint_env: str = "HUMANOID_BOT_STT_ENDPOINT") -> None:
        self._endpoint_env = endpoint_env

    def transcribe(self, audio: bytes, sample_rate: int = 16000) -> str:
        import os

        endpoint = os.environ.get(self._endpoint_env)
        if not endpoint:
            raise RuntimeError(f"Set {self._endpoint_env} to use cloud STT")
        import httpx

        response = httpx.post(
            endpoint, content=audio, headers={"Content-Type": "audio/wav"}, timeout=30
        )
        response.raise_for_status()
        return str(response.json().get("text", ""))


def create_stt(backend: str, **kwargs: str) -> SpeechToText:
    if backend == "fake":
        return FakeSTT()
    if backend == "local":
        return LocalSTT(kwargs.get("model", "base"))
    if backend == "cloud":
        return CloudSTT()
    raise ValueError(f"Unknown STT backend: {backend}")
