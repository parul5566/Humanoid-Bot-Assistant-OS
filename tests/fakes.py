"""Shared fakes for AI tests."""

from __future__ import annotations

from pydantic import BaseModel

from humanoid_bot.tools.registry import ToolDefinition, ToolRegistry
from humanoid_bot.tools.results import ToolResult


class OpenAppArgs(BaseModel):
    application: str


class CloseAppArgs(BaseModel):
    application: str


class DeleteFilesArgs(BaseModel):
    paths: list[str]


def make_registry() -> tuple[ToolRegistry, list[str]]:
    """Registry with low/medium/high tools and an execution log."""
    log: list[str] = []

    def open_app(args: OpenAppArgs) -> ToolResult:
        log.append(f"open:{args.application}")
        return {"ok": True, "summary": f"Opened {args.application}"}

    def close_app(args: CloseAppArgs) -> ToolResult:
        log.append(f"close:{args.application}")
        return {"ok": True, "summary": f"Closed {args.application}"}

    def delete_files(args: DeleteFilesArgs) -> ToolResult:
        log.append(f"delete:{len(args.paths)}")
        return {"ok": True, "summary": f"Deleted {len(args.paths)} files"}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "open_application",
            "Open an application by name",
            OpenAppArgs,
            open_app,  # type: ignore[arg-type]
        )
    )
    registry.register(
        ToolDefinition(
            "close_application",
            "Close an application by name",
            CloseAppArgs,
            close_app,  # type: ignore[arg-type]
            risk="medium",
        )
    )
    registry.register(
        ToolDefinition(
            "delete_files",
            "Delete files at the given paths",
            DeleteFilesArgs,
            delete_files,  # type: ignore[arg-type]
            risk="high",
        )
    )
    return registry, log
