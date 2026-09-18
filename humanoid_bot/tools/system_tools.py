"""System information tools via psutil."""

from __future__ import annotations

import platform
import shutil
from typing import TYPE_CHECKING, Any, cast

import psutil  # type: ignore[import-untyped]
from pydantic import BaseModel

from humanoid_bot.tools.results import ToolResult

if TYPE_CHECKING:
    from humanoid_bot.tools.registry import ToolRegistry


def system_stats() -> dict[str, Any]:
    try:
        battery = psutil.sensors_battery()
    except (FileNotFoundError, OSError, AttributeError):
        battery = None
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "battery_percent": battery.percent if battery else None,
        "battery_plugged": battery.power_plugged if battery else None,
        "network_up": any(bool(nic.isup) for nic in psutil.net_if_stats().values()),
    }


def format_stats(stats: dict[str, Any]) -> str:
    lines = [
        f"CPU: {stats['cpu_percent']:.0f}%",
        f"RAM: {stats['ram_percent']:.0f}%",
        f"Disk: {stats['disk_percent']:.0f}%",
    ]
    if stats["battery_percent"] is not None:
        plugged = "plugged in" if stats["battery_plugged"] else "on battery"
        lines.append(f"Battery: {stats['battery_percent']:.0f}% ({plugged})")
    else:
        lines.append("Battery: n/a")
    lines.append("Network: connected" if stats["network_up"] else "Network: disconnected")
    return "\n".join(lines)


class SystemInfoArgs(BaseModel):
    pass


class LockPCArgs(BaseModel):
    pass


def register_system_tools(registry: ToolRegistry) -> None:

    def system_info(args_b: BaseModel) -> ToolResult:
        _args = cast(SystemInfoArgs, args_b)
        stats = system_stats()
        return {"ok": True, "summary": format_stats(stats)}

    def detailed_info(args_b: BaseModel) -> ToolResult:
        _args = cast(SystemInfoArgs, args_b)
        total_ram = psutil.virtual_memory().total / (1024**3)
        try:
            disk_total = shutil.disk_usage("/").total / (1024**3)
        except OSError:
            disk_total = 0.0
        summary = (
            f"{platform.system()} {platform.release()} - {platform.machine()}\n"
            f"RAM total: {total_ram:.1f} GB, Disk total: {disk_total:.1f} GB\n"
            + format_stats(system_stats())
        )
        return {"ok": True, "summary": summary}

    def lock_pc(args_b: BaseModel) -> ToolResult:
        _args = cast(LockPCArgs, args_b)
        import subprocess
        import sys

        if sys.platform == "win32":
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            return {"ok": True, "summary": "PC locked."}
        return {"ok": False, "summary": "Locking is only supported on Windows."}

    from humanoid_bot.tools.registry import Risk, ToolDefinition  # noqa: PLC0415

    definitions: tuple[ToolDefinition[BaseModel], ...] = (
        ToolDefinition("system_info", "Show live CPU/RAM/disk/battery/network usage",
                       SystemInfoArgs, system_info, Risk.LOW),
        ToolDefinition("detailed_system_info", "Show detailed system information",
                       SystemInfoArgs, detailed_info, Risk.LOW),
        ToolDefinition("lock_pc", "Lock the PC (medium risk: interrupts work)",
                       LockPCArgs, lock_pc, Risk.MEDIUM),
    )
    for definition in definitions:
        registry.register(definition)
