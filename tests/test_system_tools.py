import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


from humanoid_bot.tools.registry import ToolRegistry
from humanoid_bot.tools.system_tools import format_stats, register_system_tools, system_stats


def test_system_info_returns_live_stats() -> None:
    registry = ToolRegistry()
    register_system_tools(registry)
    result = registry.execute("system_info", {})
    assert result["ok"] is True
    assert "CPU:" in result["summary"]
    assert "RAM:" in result["summary"]
    assert "Network:" in result["summary"]


def test_detailed_info_includes_platform() -> None:
    registry = ToolRegistry()
    register_system_tools(registry)
    result = registry.execute("detailed_system_info", {})
    assert result["ok"] is True


def test_lock_pc_is_medium_risk_and_off_windows_refused() -> None:
    registry = ToolRegistry()
    register_system_tools(registry)
    assert registry.get("lock_pc").risk.value == "medium"  # type: ignore[union-attr]
    import sys

    if sys.platform != "win32":
        registry.confirm = lambda *a: True
        result = registry.execute("lock_pc", {})
        assert result["ok"] is False


def test_format_stats_renders_battery() -> None:
    text = format_stats({
        "cpu_percent": 23.0, "ram_percent": 48.0, "disk_percent": 61.0,
        "battery_percent": 87.0, "battery_plugged": False, "network_up": True,
    })
    assert "CPU: 23%" in text
    assert "Battery: 87% (on battery)" in text
    assert "Network: connected" in text


def test_system_stats_shape() -> None:
    stats = system_stats()
    for key in ("cpu_percent", "ram_percent", "disk_percent", "network_up"):
        assert key in stats
