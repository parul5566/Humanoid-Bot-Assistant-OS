"""Notification tools - Windows toasts, tray-balloon fallback."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, Field

from humanoid_bot.tools.results import ToolResult

if TYPE_CHECKING:
    from humanoid_bot.tools.registry import ToolRegistry


class NotifyArgs(BaseModel):
    title: str = Field(default="Humanoid Bot", max_length=100)
    message: str = Field(min_length=1, max_length=500)


def register_notification_tools(
    registry: ToolRegistry,
    tray_notifier: Callable[[str, str], None] | None = None
) -> None:
    from humanoid_bot.tools.registry import Risk, ToolDefinition

    def notify(args_b: BaseModel) -> ToolResult:
        args = cast(NotifyArgs, args_b)
        delivered = False
        if tray_notifier is not None:
            tray_notifier(args.title, args.message)
            delivered = True
        elif _windows_toast(args.title, args.message):
            delivered = True
        if delivered:
            return {"ok": True, "summary": f"Notification shown: {args.message}"}
        return {"ok": False, "summary": "No notification backend available."}

    registry.register(
        ToolDefinition("notify", "Show a desktop notification",
                       NotifyArgs, notify, Risk.LOW)
    )


def _windows_toast(title: str, message: str) -> bool:
    import sys

    if sys.platform == "win32":
        return bool(_toast_win(title, message))
    return False


def _toast_win(title: str, message: str) -> bool:
    try:
        from winsdk.windows.data.xml.dom import XmlDocument  # type: ignore[import-not-found]
        from winsdk.windows.ui.notifications import (  # type: ignore[import-not-found]
            ToastNotification,
            ToastNotificationManager,
        )

        toast_xml = (
            "<toast><visual><binding template='ToastGeneric'>"
            f"<text>{title}</text><text>{message}</text>"
            "</binding></visual></toast>"
        )
        doc = XmlDocument()
        doc.load_xml(toast_xml)
        notifier = ToastNotificationManager.create_toast_notifier("HumanoidBot")
        notifier.show(ToastNotification(doc))
        return True
    except Exception:
        return False
