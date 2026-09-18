"""Clipboard tools: access is always announced in the returned summary."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, Field

from humanoid_bot.tools.results import ToolResult

if TYPE_CHECKING:
    from humanoid_bot.tools.registry import ToolRegistry


class ClipboardTextArgs(BaseModel):
    pass


class SummarizeClipboardArgs(BaseModel):
    max_words: int = Field(default=100, ge=20, le=500)


def _read_clipboard() -> str:
    try:
        import pyperclip  # type: ignore[import-untyped]

        return str(pyperclip.paste())
    except ImportError:
        # Qt fallback
        from PySide6.QtGui import QGuiApplication

        return str(QGuiApplication.clipboard().text())


def _write_clipboard(text: str) -> None:
    try:
        import pyperclip
    except ImportError:
        from PySide6.QtGui import QGuiApplication

        QGuiApplication.clipboard().setText(text)
        return
    pyperclip.copy(text)


def register_clipboard_tools(
    registry: ToolRegistry,
    summarize: Callable[[str], str] | None = None
) -> None:
    from humanoid_bot.tools.registry import Risk, ToolDefinition

    def read_clipboard(_args: BaseModel) -> ToolResult:
        text = _read_clipboard()
        if not text:
            return {"ok": True, "summary": "Clipboard is empty."}
        preview = text[:500]
        return {
            "ok": True,
            "summary": f"Reading clipboard ({len(text)} characters): {preview}",
        }

    def write_clipboard(args_b: BaseModel) -> ToolResult:
        args = cast(ClipboardWriteArgs, args_b)
        _write_clipboard(args.text)
        return {"ok": True, "summary": f"Wrote {len(args.text)} characters to clipboard."}

    def clear_clipboard(_args: BaseModel) -> ToolResult:
        _write_clipboard("")
        return {"ok": True, "summary": "Clipboard cleared."}

    def summarize_clipboard(args_b: BaseModel) -> ToolResult:
        cast(ClipboardTextArgs, args_b)  # validated by the registry
        text = _read_clipboard()
        if not text:
            return {"ok": False, "summary": "Clipboard is empty - nothing to summarize."}
        if summarize is None:
            return {
                "ok": False,
                "summary": "Summarization requires an AI provider to be configured.",
            }
        summary = summarize(text)
        return {"ok": True, "summary": summary}

    from pydantic import BaseModel as _BM

    class ClipboardWriteArgs(_BM):
        text: str = Field(max_length=100000)

    definitions: tuple[ToolDefinition[BaseModel], ...] = (
        ToolDefinition("read_clipboard", "Read the current clipboard contents",
                       ClipboardTextArgs, read_clipboard, Risk.LOW),
        ToolDefinition("write_clipboard", "Write text to the clipboard",
                       ClipboardWriteArgs, write_clipboard, Risk.LOW),
        ToolDefinition("clear_clipboard", "Clear the clipboard",
                       ClipboardTextArgs, clear_clipboard, Risk.LOW),
        ToolDefinition("summarize_clipboard", "Summarize the clipboard text with AI",
                       SummarizeClipboardArgs, summarize_clipboard, Risk.LOW),
    )
    for definition in definitions:
        registry.register(definition)
