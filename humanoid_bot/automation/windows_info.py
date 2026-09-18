"""Window info type shared by automation backends."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WindowInfo:
    title: str
    app_name: str
