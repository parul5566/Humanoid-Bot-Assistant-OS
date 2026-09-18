"""Voice pipeline: capture -> VAD -> STT -> callback; TTS responses.

Uses pluggable backends so the whole pipeline is testable headless (fake
audio capture). On Windows the real capture uses sounddevice.
"""

from __future__ import annotations

import collections
import io
import threading
import wave
from collections.abc import Callable
from typing import Protocol

from humanoid_bot.voice.speech_to_text import SpeechToText
from humanoid_bot.voice.text_to_speech import TextToSpeech
from humanoid_bot.voice.vad import SilenceDetector

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_BYTES = SAMPLE_RATE * 2 * FRAME_MS // 1000  # int16 mono

UtteranceCallback = Callable[[str], None]


class AudioCapture(Protocol):
    """Blocking iterator yielding int16-mono PCM frames."""

    def frames(self) -> collections.abc.Iterator[bytes]: ...
    def close(self) -> None: ...


class FakeCapture:
    """Replays pre-recorded PCM frames (used in tests / demo mode)."""

    def __init__(self, frames: list[bytes]) -> None:
        self._frames = iter(frames)

    def frames(self) -> collections.abc.Iterator[bytes]:
        return self._frames

    def close(self) -> None:
        pass


class MicCapture:
    """Microphone capture via sounddevice (lazy import)."""

    def __init__(self) -> None:
        import sounddevice as sd  # type: ignore[import-not-found]

        self._sd = sd

    def frames(self) -> collections.abc.Iterator[bytes]:
        stream = self._sd.InputStream(  # type: ignore[attr-defined,unused-ignore]
            samplerate=SAMPLE_RATE, channels=1, dtype="int16"
        )
        with stream:
            while True:
                data, _overflowed = stream.read(SAMPLE_RATE * FRAME_MS // 1000)
                yield bytes(data)

    def close(self) -> None:
        pass


class VoicePipeline:
    """Listens (push-to-talk or wake-word free-run), transcribes, responds."""

    def __init__(
        self,
        stt: SpeechToText,
        tts: TextToSpeech,
        on_utterance: UtteranceCallback,
        on_state: Callable[[str], None] | None = None,
    ) -> None:
        self.stt = stt
        self.tts = tts
        self.on_utterance = on_utterance
        self.on_state = on_state or (lambda _state: None)
        self.muted = False
        self._listening = False
        self._abort = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    def start_push_to_talk(
        self, capture: AudioCapture | None = None
    ) -> None:
        """Begin a listen-until-silence cycle on a worker thread."""
        if self._listening or self.muted:
            return
        self._listening = True
        self._abort = False
        self._thread = threading.Thread(
            target=self._listen_loop, args=(capture,), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._abort = True
        self._listening = False
        if self.tts.speaking:
            self.tts.stop()

    def set_muted(self, muted: bool) -> None:
        self.muted = muted
        if muted:
            self.stop()

    # ------------------------------------------------------------------
    def _listen_loop(self, capture: AudioCapture | None) -> None:
        try:
            text = self.listen_once(capture)
            if text:
                self.on_utterance(text)
        finally:
            self._listening = False

    def listen_once(self, capture: AudioCapture | None = None) -> str:
        """Blocking: capture until end-of-speech, return transcript."""
        cap = capture or MicCapture()
        self.on_state("listening")
        detector = SilenceDetector()
        spoken: list[bytes] = []
        try:
            for frame in cap.frames():
                verdict = detector.feed(frame, SAMPLE_RATE)
                if verdict == "speech":
                    spoken.append(frame)
                elif verdict == "end":
                    break
                if self._abort:
                    break
        finally:
            cap.close()

        if not spoken:
            self.on_state("idle")
            return ""
        audio = frames_to_wav(spoken)
        self.on_state("thinking")
        text = self.stt.transcribe(audio, SAMPLE_RATE)
        return text

    # ------------------------------------------------------------------
    def respond(self, text: str) -> None:
        """Speak a response; interruption (stop) is honored via tts.stop."""
        if self.muted:
            return
        self.on_state("speaking")
        self.tts.speak(text)
        self.on_state("idle")


def frames_to_wav(frames: list[bytes], sample_rate: int = SAMPLE_RATE) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(frames))
    return buffer.getvalue()


def silence_frames(ms: int, sample_rate: int = SAMPLE_RATE) -> list[bytes]:
    """Helper for tests: N milliseconds of digital silence frames."""
    total = sample_rate * 2 * ms // 1000
    out: list[bytes] = []
    remaining = total
    while remaining > 0:
        chunk = min(FRAME_BYTES, remaining)
        out.append(b"\x00" * chunk)
        remaining -= chunk
    return out


def speech_frames(ms: int, sample_rate: int = SAMPLE_RATE) -> list[bytes]:
    """Helper for tests: loud pseudo-speech frames (square wave at ~200Hz)."""
    out: list[bytes] = []
    total_ms = 0
    while total_ms < ms:
        frame = bytearray()
        for i in range(sample_rate * FRAME_MS // 1000):
            value = 20000 if (i // 40) % 2 == 0 else -20000
            frame += value.to_bytes(2, "little", signed=True)
        out.append(bytes(frame))
        total_ms += FRAME_MS
    return out
