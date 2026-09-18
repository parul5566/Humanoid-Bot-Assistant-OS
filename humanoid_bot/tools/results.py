"""Tool result types."""

from __future__ import annotations

from typing import NotRequired

from typing_extensions import TypedDict


class ToolResult(TypedDict):
    ok: bool
    summary: str
    detail: NotRequired[str]
