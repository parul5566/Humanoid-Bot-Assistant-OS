import pytest
from pydantic import ValidationError

from tests.fakes import OpenAppArgs, make_registry


def test_execute_low_risk_runs_without_confirmation() -> None:
    registry, log = make_registry()
    result = registry.execute("open_application", {"application": "notepad"})
    assert result["ok"] is True
    assert log == ["open:notepad"]


def test_unknown_tool_is_refused_and_audited() -> None:
    audits: list[tuple[str, ...]] = []
    registry, _ = make_registry()
    registry.audit = lambda *a: audits.append(a)
    result = registry.execute("format_c_drive", {})
    assert result["ok"] is False
    assert audits and audits[0][1] == "refused"


def test_invalid_arguments_are_refused() -> None:
    registry, log = make_registry()
    result = registry.execute("open_application", {"wrong": "args"})
    assert result["ok"] is False
    assert log == []


def test_high_risk_requires_confirmation_and_cancel_aborts() -> None:
    registry, log = make_registry()
    registry.confirm = lambda *args: False  # user declines
    result = registry.execute("delete_files", {"paths": ["a.txt"]})
    assert result["ok"] is False
    assert "cancelled" in result["summary"].lower()
    assert log == []  # nothing was deleted

    registry.confirm = lambda *args: True
    result = registry.execute("delete_files", {"paths": ["a.txt"]})
    assert result["ok"] is True
    assert log == ["delete:1"]


def test_permission_gate_blocks_tool() -> None:
    registry, log = make_registry()
    registry.permission_check = lambda name: name != "open_application"
    result = registry.execute("open_application", {"application": "x"})
    assert result["ok"] is False
    assert log == []


def test_executor_exception_is_caught() -> None:
    from humanoid_bot.tools.registry import ToolDefinition

    def boom(_args: OpenAppArgs) -> dict[str, object]:
        raise RuntimeError("disk on fire")

    registry, _ = make_registry()
    registry.register(
        ToolDefinition("boom_tool", "always fails", OpenAppArgs, boom)  # type: ignore[arg-type]
    )
    result = registry.execute("boom_tool", {"application": "x"})
    assert result["ok"] is False
    assert "disk on fire" in str(result["summary"])


def test_tool_specs_carry_risk_and_schema() -> None:
    registry, _ = make_registry()
    specs = registry.tool_specs()
    by_name = {s["function"]["name"]: s for s in specs}
    assert "[risk: high]" in by_name["delete_files"]["function"]["description"]
    props = by_name["open_application"]["function"]["parameters"]["properties"]
    assert "application" in props


def test_schema_validation_direct() -> None:
    with pytest.raises(ValidationError):
        OpenAppArgs.model_validate({"application": 123})
