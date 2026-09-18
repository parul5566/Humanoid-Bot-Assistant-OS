import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import io  # noqa: E402
import wave  # noqa: E402

from humanoid_bot.voice.pipeline import (  # noqa: E402
    FakeCapture,
    VoicePipeline,
    frames_to_wav,
    silence_frames,
    speech_frames,
)
from humanoid_bot.voice.speech_to_text import FakeSTT  # noqa: E402
from humanoid_bot.voice.text_to_speech import FakeTTS  # noqa: E402
from humanoid_bot.voice.vad import EnergyVAD, SilenceDetector  # noqa: E402
from humanoid_bot.voice.wake_word import WakeWordDetector  # noqa: E402


def make_pipeline(states: list[str]) -> "tuple[VoicePipeline, list[str]]":
    heard: list[str] = []
    pipeline = VoicePipeline(
        stt=FakeSTT(responses=["open notepad"]),
        tts=FakeTTS(),
        on_utterance=heard.append,
        on_state=states.append,
    )
    return pipeline, heard


def test_energy_vad_detects_speech_and_silence() -> None:
    vad = EnergyVAD()
    assert vad.is_speech(speech_frames(30)[0]) is True
    assert vad.is_speech(silence_frames(30)[0]) is False


def test_silence_detector_reports_end_after_silence() -> None:
    detector = SilenceDetector(silence_ms=300)
    verdicts = [detector.feed(f) for f in speech_frames(300)]
    assert "speech" in verdicts
    tail = [detector.feed(f) for f in silence_frames(400)]
    assert "end" in tail


def test_pipeline_full_cycle() -> None:
    states: list[str] = []
    pipeline, heard = make_pipeline(states)
    frames = speech_frames(400) + silence_frames(1000)
    text = pipeline.listen_once(FakeCapture(frames))
    assert text == "open notepad"
    pipeline.on_utterance(text)
    pipeline.respond("Opening Notepad.")
    assert heard == ["open notepad"]
    assert states == ["listening", "thinking", "speaking", "idle"]


def test_pipeline_mute_blocks_listening_and_speaking() -> None:
    states: list[str] = []
    pipeline, heard = make_pipeline(states)
    pipeline.set_muted(True)
    pipeline.start_push_to_talk(FakeCapture(speech_frames(100)))
    pipeline.respond("hello")
    assert heard == []
    assert "speaking" not in states
    assert pipeline.tts.utterances == []


def test_barge_in_stops_speaking() -> None:
    pipeline, _heard = make_pipeline([])
    pipeline.tts.utterances.append("long speech")
    pipeline.stop()  # should call tts.stop without error
    assert pipeline.tts.speaking is False


def test_frames_to_wav_produces_valid_wav() -> None:
    frames = speech_frames(60)
    wav_bytes = frames_to_wav(frames)
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 16000
        assert wav.getnframes() > 0


def test_fake_tts_records_utterances() -> None:
    tts = FakeTTS()
    tts.speak("one")
    tts.speak("two")
    assert tts.utterances == ["one", "two"]


def test_wake_word_match_and_strip() -> None:
    detector = WakeWordDetector(stt=FakeSTT(), phrase="hey bot")
    assert detector.matches("Hey Bot, open Chrome") is True
    assert detector.matches("open Chrome") is False
    assert detector.strip_wake_word("Hey Bot, open Chrome") == "open Chrome"
    assert detector.strip_wake_word("no wake word here") == "no wake word here"
