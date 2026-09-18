
from humanoid_bot.ai.providers.base import ChatResult, FakeProvider
from humanoid_bot.tools.registry import ToolRegistry
from humanoid_bot.tools.screen_tools import register_screen_tools
from humanoid_bot.vision.ocr import FakeOcrEngine
from humanoid_bot.vision.screen_capture import (
    FakeScreenCapture,
    ScreenCapture,
    decode_png,
)
from humanoid_bot.vision.vision_analyzer import VisionAnalyzer


class DenyCapture(ScreenCapture):
    def capture(self, monitor: int = 1) -> bytes:
        raise PermissionError("screen access denied by user")


def make(capture=None, ocr=None, provider=None) -> ToolRegistry:
    registry = ToolRegistry()
    register_screen_tools(
        registry,
        capture or FakeScreenCapture(),
        ocr or FakeOcrEngine("Hello screen text"),
        VisionAnalyzer(provider),
    )
    return registry


def test_read_screen_text_via_ocr() -> None:
    registry = make(ocr=FakeOcrEngine("line one\nline two"))
    result = registry.execute("read_screen_text", {})
    assert result["ok"] is True
    assert "line one" in result["summary"]


def test_read_screen_text_no_text_found() -> None:
    registry = make(ocr=FakeOcrEngine(""))
    result = registry.execute("read_screen_text", {})
    assert result["ok"] is False


def test_whats_on_screen_uses_vision_provider() -> None:
    provider = FakeProvider(script=[ChatResult(text="A code editor with Python.")])
    registry = make(provider=provider)
    result = registry.execute("whats_on_my_screen", {"question": "what is this?"})
    assert result["ok"] is True
    assert "code editor" in result["summary"]


def test_whats_on_screen_ocr_fallback_without_provider() -> None:
    registry = make(ocr=FakeOcrEngine("fallback text"))
    result = registry.execute("whats_on_my_screen", {})
    assert result["ok"] is True
    assert "fallback text" in result["detail"]


def test_capture_denied_returns_error_not_crash() -> None:
    registry = make(capture=DenyCapture())
    result = registry.execute("read_screen_text", {})
    assert result["ok"] is False
    assert "denied" in result["summary"]


def test_fake_capture_produces_valid_png() -> None:
    png = FakeScreenCapture(64, 32).capture()
    width, height, _raw = decode_png(png)
    assert (width, height) == (64, 32)


def test_vision_analyzer_returns_none_without_provider() -> None:
    analyzer = VisionAnalyzer(None)
    assert analyzer.describe(b"png", "q") is None


def test_screen_tools_are_low_risk() -> None:
    registry = make()
    for name in ("whats_on_my_screen", "read_screen_text"):
        assert registry.get(name) is not None  # type: ignore[union-attr]
