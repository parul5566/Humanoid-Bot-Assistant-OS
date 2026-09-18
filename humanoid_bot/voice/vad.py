"""Voice activity detection.

Simple energy-based VAD over int16 PCM frames. A pluggable Protocol keeps
the door open for ML-based VADs (e.g. webrtcvad / silero) later.
"""

from __future__ import annotations

try:  # Python < 3.13
    import audioop
except ImportError:  # Python >= 3.13: audioop moved to audioop-lts
    try:
        import audioop_lts as audioop  # type: ignore[import-not-found,no-redef]
    except ImportError:  # final fallback: tiny pure-python RMS
        class _AudioOp:
            @staticmethod
            def rms(frame: bytes, width: int) -> int:
                count = len(frame) // width
                if count == 0:
                    return 0
                total = sum(
                    int.from_bytes(frame[i : i + width], "little", signed=True)
                    for i in range(0, len(frame), width)
                )
                return int((total * total // count) ** 0.5)

        audioop = _AudioOp()  # type: ignore[assignment]

from typing import Protocol


class VoiceActivityDetector(Protocol):
    def is_speech(self, frame: bytes, sample_rate: int = 16000) -> bool: ...


class EnergyVAD:
    """RMS-threshold voice activity detector."""

    def __init__(self, rms_threshold: int = 500) -> None:
        self.rms_threshold = rms_threshold

    def is_speech(self, frame: bytes, sample_rate: int = 16000) -> bool:
        if not frame:
            return False
        rms = audioop.rms(frame, 2)  # 2 = 16-bit samples
        return rms >= self.rms_threshold


class SilenceDetector:
    """Accumulates frames and reports end-of-utterance after N silent ms."""

    def __init__(
        self,
        vad: VoiceActivityDetector | None = None,
        silence_ms: int = 900,
        max_utterance_ms: int = 15000,
    ) -> None:
        self.vad = vad or EnergyVAD()
        self.silence_ms = silence_ms
        self.max_utterance_ms = max_utterance_ms
        self._silent_run_ms = 0.0
        self._utterance_ms = 0.0

    def reset(self) -> None:
        self._silent_run_ms = 0.0
        self._utterance_ms = 0.0

    def feed(self, frame: bytes, sample_rate: int = 16000) -> str:
        """Process one frame. Returns 'speech' | 'silence' | 'end'."""
        frame_ms = 1000 * len(frame) / 2 / sample_rate  # int16 mono
        self._utterance_ms += frame_ms
        if self.vad.is_speech(frame, sample_rate):
            self._silent_run_ms = 0.0
            return "speech"
        self._silent_run_ms += frame_ms
        if self._silent_run_ms >= self.silence_ms and self._utterance_ms > self.silence_ms:
            self.reset()
            return "end"
        if self._utterance_ms >= self.max_utterance_ms:
            self.reset()
            return "end"
        return "silence"
