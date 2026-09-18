from humanoid_bot.app.config import AppConfig


def test_defaults() -> None:
    cfg = AppConfig()
    assert cfg.general.theme == "dark"
    assert cfg.ai.provider == "openai"
    assert cfg.privacy.allow_screen_access is False  # opt-in security default


def test_roundtrip(tmp_path) -> None:
    cfg = AppConfig()
    cfg.ai.temperature = 0.7
    cfg.privacy.allow_clipboard = False
    data = cfg.model_dump()
    restored = AppConfig.model_validate(data)
    assert restored.ai.temperature == 0.7
    assert restored.privacy.allow_clipboard is False
