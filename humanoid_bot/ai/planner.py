"""Task planner: multi-step requests decomposed into ordered tool calls.

The planner asks the LLM for a JSON step plan, validates every step against
the tool registry, then executes step-by-step with progress reporting.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from pydantic import BaseModel, ValidationError

from humanoid_bot.ai.providers.base import LLMProvider, Message
from humanoid_bot.tools.registry import ToolRegistry

PLANNER_PROMPT = """Decompose the user's request into an ordered list of tool \
steps using ONLY tools from the catalog. Respond with strict JSON:
{"steps": [{"tool": "<name>", "arguments": {...}, "why": "<short reason>"}]}
No prose. If the request is a single simple action, return one step."""


class PlanStep(BaseModel):
    tool: str
    arguments: dict[str, object] = {}
    why: str = ""


class Plan(BaseModel):
    steps: list[PlanStep]


class ExecutionReport:
    def __init__(self) -> None:
        self.completed: list[str] = []
        self.failed: list[str] = []
        self.cancelled = False

    @property
    def ok(self) -> bool:
        return not self.failed and not self.cancelled


class Planner:
    def __init__(
        self,
        provider: LLMProvider,
        registry: ToolRegistry,
        confirm_each_step: bool = True,
        on_progress: Callable[[int, int, str], None] | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.confirm_each_step = confirm_each_step
        self.on_progress = on_progress or (lambda *_a: None)

    # ------------------------------------------------------------------
    def make_plan(self, user_text: str) -> Plan:
        response = self.provider.chat(
            [Message(role="system", content=PLANNER_PROMPT),
             Message(role="user", content=user_text)],
            tools=[],  # planning happens in JSON, not function-calling
        )
        try:
            data = json.loads(response.text or "{}")
            return Plan.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            return Plan(steps=[])

    def validate_plan(self, plan: Plan) -> list[str]:
        """Return problems: unknown tools or schemas that cannot validate."""
        problems: list[str] = []
        for i, step in enumerate(plan.steps, 1):
            tool = self.registry.get(step.tool)
            if tool is None:
                problems.append(f"Step {i}: unknown tool '{step.tool}'")
                continue
            try:
                tool.validate(step.arguments)
            except ValidationError as exc:
                problems.append(f"Step {i}: invalid arguments - {exc.errors()[:2]}")
        return problems

    def execute_plan(self, plan: Plan) -> ExecutionReport:
        report = ExecutionReport()
        total = len(plan.steps)
        for i, step in enumerate(plan.steps, 1):
            self.on_progress(i, total, step.why or step.tool)
            outcome = self.registry.execute(step.tool, step.arguments)
            if outcome.get("ok"):
                report.completed.append(outcome.get("summary", step.tool))
            elif "cancelled" in outcome.get("summary", "").lower():
                report.cancelled = True
                break
            else:
                report.failed.append(outcome.get("summary", step.tool))
        return report

    def plan_and_run(self, user_text: str) -> ExecutionReport | None:
        """Plan, validate, run. Returns None if no valid plan could be made."""
        plan = self.make_plan(user_text)
        if not plan.steps or self.validate_plan(plan):
            return None
        return self.execute_plan(plan)
