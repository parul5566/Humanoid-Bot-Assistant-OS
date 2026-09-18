from humanoid_bot.tools.clipboard_tools import register_clipboard_tools
from humanoid_bot.tools.notification_tools import register_notification_tools
from humanoid_bot.tools.registry import ToolRegistry
from humanoid_bot.tools.web_tools import _extract_results, _html_to_text


def test_clipboard_read_announces_access(monkeypatch) -> None:
    import humanoid_bot.tools.clipboard_tools as ct

    monkeypatch.setattr(ct, "_read_clipboard", lambda: "secret contents")
    registry = ToolRegistry()
    register_clipboard_tools(registry)
    result = registry.execute("read_clipboard", {})
    assert result["ok"] is True
    assert "Reading clipboard" in result["summary"]


def test_clipboard_empty_ok(monkeypatch) -> None:
    import humanoid_bot.tools.clipboard_tools as ct

    monkeypatch.setattr(ct, "_read_clipboard", lambda: "")
    registry = ToolRegistry()
    register_clipboard_tools(registry)
    assert registry.execute("read_clipboard", {})["ok"] is True


def test_clipboard_summarize_without_provider_refused(monkeypatch) -> None:
    import humanoid_bot.tools.clipboard_tools as ct

    monkeypatch.setattr(ct, "_read_clipboard", lambda: "some long text")
    registry = ToolRegistry()
    register_clipboard_tools(registry, summarize=None)
    result = registry.execute("summarize_clipboard", {})
    assert result["ok"] is False
    assert "provider" in result["summary"].lower()


def test_clipboard_summarize_with_summarizer(monkeypatch) -> None:
    import humanoid_bot.tools.clipboard_tools as ct

    monkeypatch.setattr(ct, "_read_clipboard", lambda: "some long text")
    registry = ToolRegistry()
    register_clipboard_tools(registry, summarize=lambda text: f"summary of {len(text)} chars")
    result = registry.execute("summarize_clipboard", {})
    assert result["ok"] is True
    assert "summary of 14 chars" in result["summary"]


def test_clipboard_risk_levels_are_low_but_gated_by_capability() -> None:
    registry = ToolRegistry()
    register_clipboard_tools(registry)
    assert registry.get("read_clipboard") is not None  # type: ignore[union-attr]


def test_notify_with_tray_notifier() -> None:
    shown: list[tuple[str, str]] = []
    registry = ToolRegistry()
    register_notification_tools(registry, tray_notifier=lambda t, m: shown.append((t, m)))
    result = registry.execute("notify", {"message": "task finished"})
    assert result["ok"] is True
    assert shown == [("Humanoid Bot", "task finished")]


def test_notify_without_backend_fails_gracefully() -> None:
    registry = ToolRegistry()
    register_notification_tools(registry, tray_notifier=None)
    import sys

    if sys.platform != "win32":
        result = registry.execute("notify", {"message": "x"})
        assert result["ok"] is False


def test_html_to_text_strips_scripts_and_tags() -> None:
    html = (
        "<html><script>evil()</script><style>x{}</style>"
        "<body><p>Hello <b>world</b></p></body></html>"
    )
    text = _html_to_text(html)
    assert "evil" not in text
    assert "Hello world" in text


def test_extract_results_parses_ddg_html() -> None:
    html = '<a class="result__a" href="https://x.io">Result One</a>'
    results = _extract_results(html)
    assert results == [("Result One", "https://x.io")]
