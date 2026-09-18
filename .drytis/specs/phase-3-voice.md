# Phase 3 — Voice

## Goal
Full voice pipeline: mic → VAD → STT → text into orchestrator; TTS responses; push-to-talk; mute; interruptible speech.

## Files
- `humanoid_bot/voice/speech_to_text.py` — pluggable backends (cloud STT; local via faster-whisper/Vosk where available), fake backend for CI
- `humanoid_bot/voice/text_to_speech.py` — pluggable TTS (SAPI/winsdk on Windows, pyttsx3/espeak fallback, fake for CI)
- `humanoid_bot/voice/vad.py` — voice activity detection, end-of-silence detection
- `humanoid_bot/voice/wake_word.py` — optional wake word ("Hey Bot"), off by default
- `humanoid_bot/voice/pipeline.py` — async pipeline wiring voice → orchestrator → TTS, supports barge-in (interrupt TTS by speaking)

## Acceptance Criteria
- [ ] Push-to-talk (mic button or Ctrl+Shift+V held) captures speech and the transcript appears in chat
- [ ] Assistant responses are spoken aloud; speaking stops immediately when interrupted
- [ ] Mic mute toggle stops all capture
- [ ] STT/TTS backends are switchable in settings; fake backend works headless in tests
- [ ] Pipeline tests pass on Linux using fake backends
