"""App / keyboard / mouse tools registered on the ToolRegistry."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel, Field

from humanoid_bot.automation.app_registry import AppRegistry
from humanoid_bot.tools.registry import Risk, ToolDefinition, ToolRegistry
from humanoid_bot.tools.results import ToolResult
from humanoid_bot.tools.typing import AnyBackend


class OpenAppArgs(BaseModel):
    application: str = Field(description="Application name, e.g. 'notepad'")


class CloseAppArgs(BaseModel):
    application: str


class TypeTextArgs(BaseModel):
    text: str = Field(max_length=10000)


class PressKeyArgs(BaseModel):
    key: str = Field(description="Key name, e.g. 'enter', 'f5'")


class HotkeyArgs(BaseModel):
    keys: list[str] = Field(min_length=2, max_length=4)


class ClickArgs(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    button: str = Field(default="left", pattern="^(left|right|middle)$")


class MoveMouseArgs(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class ReadWindowArgs(BaseModel):
    title: str


class ListWindowsArgs(BaseModel):
    query: str = ""


def register_automation_tools(
    registry: ToolRegistry,
    backend: AnyBackend,
    apps: AppRegistry,
) -> None:
    def open_application(args_b: BaseModel) -> ToolResult:
        args = cast(OpenAppArgs, args_b)
        entry = apps.resolve(args.application)
        if entry is None:
            return {
                "ok": False,
                "summary": f"I couldn't find '{args.application}'. "
                "Would you like me to search for its installed location?",
                "detail": f"Known apps: {', '.join(apps.all_names())}",
            }
        backend.launch(entry.executable, entry.args)
        return {"ok": True, "summary": f"Opening {entry.display}."}

    def close_application(args_b: BaseModel) -> ToolResult:
        args = cast(CloseAppArgs, args_b)
        entry = apps.resolve(args.application)
        name = entry.display if entry else args.application
        closed = backend.close_app(name)
        if not closed:
            return {"ok": False, "summary": f"No running window found for {name}."}
        return {"ok": True, "summary": f"Closed {name}."}

    def type_text(args_b: BaseModel) -> ToolResult:
        args = cast(TypeTextArgs, args_b)
        backend.type_text(args.text)
        return {"ok": True, "summary": f"Typed {len(args.text)} characters."}

    def press_key(args_b: BaseModel) -> ToolResult:
        args = cast(PressKeyArgs, args_b)
        backend.press_key(args.key)
        return {"ok": True, "summary": f"Pressed {args.key}."}

    def hotkey(args_b: BaseModel) -> ToolResult:
        args = cast(HotkeyArgs, args_b)
        backend.hotkey(args.keys)
        return {"ok": True, "summary": f"Pressed {'+'.join(args.keys)}."}

    def click(args_b: BaseModel) -> ToolResult:
        args = cast(ClickArgs, args_b)
        backend.click(args.x, args.y, args.button)
        return {"ok": True, "summary": f"Clicked ({args.x}, {args.y})."}

    def move_mouse(args_b: BaseModel) -> ToolResult:
        args = cast(MoveMouseArgs, args_b)
        backend.move_mouse(args.x, args.y)
        return {"ok": True, "summary": f"Moved mouse to ({args.x}, {args.y})."}

    def read_window(args_b: BaseModel) -> ToolResult:
        args = cast(ReadWindowArgs, args_b)
        content = backend.read_window(args.title)
        if not content:
            return {"ok": False, "summary": f"Couldn't read a window titled '{args.title}'."}
        return {"ok": True, "summary": content[:2000]}

    def list_windows(args_b: BaseModel) -> ToolResult:
        args = cast(ListWindowsArgs, args_b)
        windows = backend.find_windows(args.query) if args.query else [backend.active_window()]
        if not windows:
            return {"ok": False, "summary": "No matching windows found."}
        titles = "; ".join(w.title for w in windows[:10])
        return {"ok": True, "summary": titles}

    definitions: tuple[ToolDefinition[BaseModel], ...] = (
        ToolDefinition("open_application", "Open an application by name",
                       OpenAppArgs, open_application, Risk.LOW),
        ToolDefinition("close_application", "Close an application (may lose unsaved work)",
                       CloseAppArgs, close_application, Risk.MEDIUM),
        ToolDefinition("type_text", "Type text into the active window",
                       TypeTextArgs, type_text, Risk.LOW),
        ToolDefinition("press_key", "Press a keyboard key",
                       PressKeyArgs, press_key, Risk.LOW),
        ToolDefinition("hotkey", "Press a key combination",
                       HotkeyArgs, hotkey, Risk.LOW),
        ToolDefinition("click", "Click at screen coordinates",
                       ClickArgs, click, Risk.LOW),
        ToolDefinition("move_mouse", "Move the mouse cursor",
                       MoveMouseArgs, move_mouse, Risk.LOW),
        ToolDefinition("read_window", "Read the title/content of a window",
                       ReadWindowArgs, read_window, Risk.LOW),
        ToolDefinition("list_windows", "List matching open windows",
                       ListWindowsArgs, list_windows, Risk.LOW),
    )
    for definition in definitions:
        registry.register(definition)
