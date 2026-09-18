from humanoid_bot.automation.app_registry import AppEntry, AppRegistry
from humanoid_bot.automation.backends import FakeBackend, get_backend
from humanoid_bot.tools.automation_tools import register_automation_tools
from humanoid_bot.tools.registry import ToolRegistry


def make_tools() -> tuple[ToolRegistry, FakeBackend, AppRegistry]:
    backend = FakeBackend()
    apps = AppRegistry()
    registry = ToolRegistry()
    register_automation_tools(registry, backend, apps)
    return registry, backend, apps


def test_registry_resolves_names_and_aliases() -> None:
    apps = AppRegistry()
    assert apps.resolve("notepad").name == "notepad"  # type: ignore[union-attr]
    assert apps.resolve("VS Code").name == "code"  # type: ignore[union-attr]
    assert apps.resolve("google chrome").name == "chrome"  # type: ignore[union-attr]
    assert apps.resolve("doesnotexist") is None


def test_registry_user_entries_override() -> None:
    apps = AppRegistry()
    apps.add(AppEntry(name="myapp", display="My App", executable="myapp.exe",
                      aliases=["tool"]))
    assert apps.resolve("tool").name == "myapp"  # type: ignore[union-attr]
    assert apps.remove("myapp") is True
    assert apps.resolve("myapp") is None


def test_open_application_launches_via_backend() -> None:
    registry, backend, _apps = make_tools()
    result = registry.execute("open_application", {"application": "notepad"})
    assert result["ok"] is True
    assert backend.launched == [("notepad.exe", [])]


def test_open_unknown_app_triggers_recovery_message() -> None:
    registry, backend, _apps = make_tools()
    result = registry.execute("open_application", {"application": "frobnicator"})
    assert result["ok"] is False
    assert "couldn't find" in result["summary"]
    assert backend.launched == []


def test_close_application_medium_risk_needs_confirmation() -> None:
    registry, backend, _apps = make_tools()
    registry.confirm = lambda *a: False
    result = registry.execute("close_application", {"application": "notepad"})
    assert result["ok"] is False
    assert backend.closed == []

    registry.confirm = lambda *a: True
    result = registry.execute("close_application", {"application": "notepad"})
    assert result["ok"] is True
    assert backend.closed == ["Notepad"]


def test_close_app_no_window_fails_gracefully() -> None:
    registry, backend, _apps = make_tools()
    backend.fail_close_for = ["Notepad"]  # close_app reports nothing closed
    registry.confirm = lambda *a: True
    result = registry.execute("close_application", {"application": "notepad"})
    assert result["ok"] is False
    assert "no running window" in result["summary"].lower()


def test_keyboard_and_mouse_tools_record_operations() -> None:
    registry, backend, _apps = make_tools()
    assert registry.execute("type_text", {"text": "hello world"})["ok"] is True
    assert registry.execute("press_key", {"key": "enter"})["ok"] is True
    assert registry.execute("hotkey", {"keys": ["ctrl", "s"]})["ok"] is True
    assert registry.execute("click", {"x": 100, "y": 200})["ok"] is True
    assert registry.execute("move_mouse", {"x": 5, "y": 6})["ok"] is True
    assert backend.typed == ["hello world"]
    assert backend.keys == ["enter"]
    assert backend.hotkeys == [["ctrl", "s"]]
    assert backend.clicks == [(100, 200, "left")]


def test_click_rejects_invalid_button_and_negative_coords() -> None:
    registry, backend, _apps = make_tools()
    assert registry.execute("click", {"x": -1, "y": 0})["ok"] is False
    assert registry.execute("click", {"x": 1, "y": 1, "button": "laser"})["ok"] is False
    assert backend.clicks == []


def test_window_tools_use_fake_backend_windows() -> None:
    registry, _backend, _apps = make_tools()
    result = registry.execute("list_windows", {"query": "notepad"})
    assert result["ok"] is True
    assert "Notepad" in result["summary"]
    assert registry.execute("read_window", {"title": "nope"})["ok"] is False


def test_all_automation_tools_registered_with_expected_risk() -> None:
    registry, _backend, _apps = make_tools()
    assert registry.get("open_application").risk.value == "low"  # type: ignore[union-attr]
    assert registry.get("close_application").risk.value == "medium"  # type: ignore[union-attr]
    for name in ("open_application", "close_application", "type_text", "press_key",
                 "hotkey", "click", "move_mouse", "read_window", "list_windows"):
        assert registry.get(name) is not None


def test_backend_factory_uses_fake_on_linux() -> None:
    import sys

    if sys.platform != "win32":
        assert get_backend() is not None
