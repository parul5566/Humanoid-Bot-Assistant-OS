from humanoid_bot.ai.memory import Memory
from humanoid_bot.ai.orchestrator import Orchestrator
from humanoid_bot.ai.planner import Planner
from humanoid_bot.ai.providers.base import ChatResult, FakeProvider, ToolCall
from humanoid_bot.storage.database import Database
from tests.fakes import make_registry


def make_orchestrator(script: list[ChatResult]) -> tuple[Orchestrator, FakeProvider, list[str]]:
    provider = FakeProvider(script=script)
    registry, log = make_registry()
    db = Database.open(":memory:")
    memory = Memory(db)
    orch = Orchestrator(provider, registry, memory)
    return orch, provider, log


def test_simple_text_reply() -> None:
    orch, _provider, _log = make_orchestrator([ChatResult(text="Hello!")])
    reply = orch.handle_user_text("hi")
    assert reply == "Hello!"


def test_tool_call_round_trip() -> None:
    script = [
        ChatResult(
            tool_calls=[ToolCall(id="c1", name="open_application",
                                 arguments={"application": "notepad"})]
        ),
        ChatResult(text="Opened Notepad for you."),
    ]
    orch, provider, log = make_orchestrator(script)
    reply = orch.handle_user_text("open notepad")
    assert reply == "Opened Notepad for you."
    assert log == ["open:notepad"]
    # The tool result was fed back to the provider in the second call.
    second_call = provider.calls[1]
    assert any(m.role == "tool" for m in second_call)


def test_unknown_tool_does_not_crash_and_is_reported() -> None:
    script = [
        ChatResult(tool_calls=[ToolCall(id="c2", name="make_coffee", arguments={})]),
        ChatResult(text="I could not do that."),
    ]
    orch, _provider, _log = make_orchestrator(script)
    reply = orch.handle_user_text("make coffee")
    assert reply == "I could not do that."  # graceful


def test_memory_records_turns() -> None:
    orch, _provider, _log = make_orchestrator([ChatResult(text="ok")])
    orch.handle_user_text("hello")
    convo = orch.memory.conversation()
    assert convo[0] == ("user", "hello")
    assert convo[-1] == ("assistant", "ok")


def test_memory_persistence_long_term_gated() -> None:
    db = Database.open(":memory:")
    memory = Memory(db, long_term_enabled=False)
    assert memory.store_long_term("secret fact") is False
    assert memory.entries("long_term") == []
    memory.long_term_enabled = True
    assert memory.store_long_term("user likes dark theme") is True
    assert len(memory.entries("long_term")) == 1
    memory.clear("long_term")
    assert memory.entries("long_term") == []


# --- Planner -------------------------------------------------------


def test_planner_executes_valid_multi_step_plan() -> None:
    plan_json = (
        '{"steps": ['
        '{"tool": "open_application", "arguments": {"application": "code"}, "why": "editor"}, '
        '{"tool": "open_application", "arguments": {"application": "chrome"}, "why": "docs"}]}'
    )
    provider = FakeProvider(script=[ChatResult(text=plan_json)])
    registry, log = make_registry()
    progress: list[tuple[int, int, str]] = []
    planner = Planner(provider, registry, on_progress=lambda i, n, w: progress.append((i, n, w)))
    report = planner.plan_and_run("prepare my workspace")
    assert report is not None and report.ok
    assert log == ["open:code", "open:chrome"]
    assert [(i, n) for i, n, _w in progress] == [(1, 2), (2, 2)]
    assert [w for _i, _n, w in progress] == ["editor", "docs"]


def test_planner_rejects_plan_with_unknown_tool() -> None:
    provider = FakeProvider(script=[
        ChatResult(text='{"steps": [{"tool": "launch_missiles", "arguments": {}}]}')
    ])
    registry, _log = make_registry()
    planner = Planner(provider, registry)
    assert planner.plan_and_run("do it") is None


def test_planner_rejects_malformed_json() -> None:
    provider = FakeProvider(script=[ChatResult(text="not json at all")])
    registry, _ = make_registry()
    planner = Planner(provider, registry)
    assert planner.plan_and_run("anything") is None


def test_planner_stops_on_cancelled_step() -> None:
    provider = FakeProvider(script=[
        ChatResult(text='{"steps": ['
                        '{"tool": "delete_files", "arguments": {"paths": ["a"]}},'
                        '{"tool": "open_application", "arguments": {"application": "x"}}]}')
    ])
    registry, log = make_registry()
    registry.confirm = lambda *a: False  # user declines the delete
    planner = Planner(provider, registry)
    report = planner.execute_plan(planner.make_plan("clean up"))
    assert report.cancelled
    assert log == []  # the later step never ran
