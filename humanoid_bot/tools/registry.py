"""Tool registry core: typed tools with risk levels and validated execution.

The registry's execute() path is the ONLY way tools run. It enforces:
1. Tool must exist (no hallucinated names).
2. Arguments must validate against the tool's pydantic schema.
3. Permission manager gate + confirmation for medium/high risk.
4. Audit log entry for every attempt (executed, refused, cancelled, error).
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any, cast

from pydantic import BaseModel, ValidationError

from humanoid_bot.tools.results import ToolResult


class Risk(StrEnum):
    LOW = "low"        # auto-execute (open app, read system info, search)
    MEDIUM = "medium"  # confirm (move/rename files, close apps, settings)
    HIGH = "high"      # always explicit confirm (delete, install, admin)


ConfirmationCallback = Callable[[str, str, str], bool]
"""(tool_name, risk, summary_of_targets) -> bool (True = confirmed)."""

PermissionCheck = Callable[[str], bool]
"""(tool_name) -> bool (True = permission granted)."""

AuditSink = Callable[[str, str, str, str], None]
"""(tool, decision, risk, arguments_summary) -> None."""


class ToolDefinition[TArgs: BaseModel]:
    """A registered tool: typed schema, risk level, and executor."""

    def __init__(
        self,
        name: str,
        description: str,
        args_model: type[BaseModel],
        executor: Callable[[BaseModel], ToolResult],
        risk: Risk | str = Risk.LOW,
    ) -> None:
        self.name = name
        self.description = description
        self.args_model = args_model
        self.executor = executor
        self.risk = Risk(risk)

    def validate(self, arguments: dict[str, Any]) -> TArgs:
        return cast(TArgs, self.args_model.model_validate(arguments))


class ToolRegistry:
    """Heterogeneous tool storage; register() accepts any ToolDefinition."""

    def __init__(
        self,
        permission_check: PermissionCheck = lambda _name: True,
        confirm: ConfirmationCallback = lambda *_args: True,
        audit: AuditSink = lambda *_args: None,
    ) -> None:
        self._tools: dict[str, ToolDefinition[BaseModel]] = {}
        self.permission_check = permission_check
        self.confirm = confirm
        self.audit = audit

    # ------------------------------------------------------------------
    def register(self, tool: ToolDefinition[BaseModel]) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition[BaseModel] | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def tool_specs(self) -> list[dict[str, Any]]:
        """OpenAI-style function specs for the LLM providers."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": f"[risk: {tool.risk.value}] {tool.description}",
                    "parameters": tool.args_model.model_json_schema(),
                },
            }
            for tool in sorted(self._tools.values(), key=lambda t: t.name)
        ]

    # ------------------------------------------------------------------
    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            self.audit(name, "refused", "low", "unknown tool")
            return {
                "ok": False,
                "summary": f"Unknown tool '{name}'.",
                "detail": "The requested action does not exist in the tool catalog.",
            }

        args_summary = str(arguments)[:200]

        if not self.permission_check(name):
            self.audit(name, "refused", tool.risk.value, args_summary)
            return {
                "ok": False,
                "summary": f"Permission for '{name}' is disabled in settings.",
            }

        try:
            validated = tool.validate(arguments)
        except ValidationError as exc:
            self.audit(name, "refused", tool.risk.value, args_summary)
            return {
                "ok": False,
                "summary": "Invalid arguments for the requested action.",
                "detail": str(exc.errors()[:3]),
            }

        if tool.risk is not Risk.LOW:
            summary = str(validated.model_dump())[:300]
            if not self.confirm(name, tool.risk.value, summary):
                self.audit(name, "cancelled", tool.risk.value, args_summary)
                return {"ok": False, "summary": "Action cancelled by the user."}

        try:
            result = tool.executor(validated)
        except Exception as exc:  # noqa: BLE001 - tools must never crash the app
            self.audit(name, "error", tool.risk.value, args_summary)
            return {"ok": False, "summary": f"Action failed: {exc}"}

        decision = "executed" if result.get("ok") else "error"
        self.audit(name, decision, tool.risk.value, args_summary)
        return result
