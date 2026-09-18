"""Typed application configuration loaded from an optional JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from humanoid_bot.app.paths import app_data_dir

Theme = Literal["light", "dark", "system"]


class VoiceConfig(BaseModel):
    stt_backend: Literal["fake", "local", "cloud"] = "fake"
    tts_backend: Literal["fake", "local", "cloud"] = "fake"
    stt_model: str = "base"
    tts_voice: str = ""
    tts_rate: float = 1.0
    wake_word_enabled: bool = False
    wake_word: str = "hey bot"
    push_to_talk: bool = True
    muted: bool = False


class AIConfig(BaseModel):
    provider: Literal["openai", "ollama", "fake"] = "openai"
    model: str = "gpt-4o-mini"
    base_url: str | None = None
    api_key_env: str = "HUMANOID_BOT_API_KEY"
    temperature: float = 0.3
    max_context_messages: int = 20


class PrivacyConfig(BaseModel):
    model_config = {"extra": "forbid"}
    allow_screen_access: bool = False
    allow_microphone: bool = True
    allow_clipboard: bool = True
    allow_file_access: bool = True
    long_term_memory: bool = False


class GeneralConfig(BaseModel):
    theme: Theme = "dark"
    always_on_top: bool = False
    start_with_windows: bool = False
    language: str = "en"


class AppConfig(BaseModel):
    """Root configuration. Secrets are NEVER stored here - only env var names."""

    general: GeneralConfig = Field(default_factory=GeneralConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)

    @classmethod
    def load(cls) -> AppConfig:
        path = cls.config_path()
        if path.exists():
            return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))
        return cls()

    def save(self) -> None:
        path = self.config_path()
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @staticmethod
    def config_path() -> Path:
        return app_data_dir() / "config.json"
