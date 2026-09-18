"""Optional wake word listener (off by default).

Simple substring detector over a continuously transcribed stream. When no
local STT is available this stays disabled - push-to-talk is the default
interaction.
"""

from __future__ import annotations

from humanoid_bot.voice.speech_to_text import SpeechToText


class WakeWordDetector:
    def __init__(self, stt: SpeechToText, phrase: str = "hey bot") -> None:
        self.stt = stt
        self.phrase = phrase.lower()

    def matches(self, transcript: str) -> bool:
        return self.phrase in transcript.lower()

    def strip_wake_word(self, transcript: str) -> str:
        lowered = transcript.lower()
        idx = lowered.find(self.phrase)
        if idx == -1:
            return transcript
        return transcript[idx + len(self.phrase) :].strip(" ,.!?")
