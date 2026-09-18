"""Audit log facade over the AuditLog table (append-only by convention)."""

from __future__ import annotations

from humanoid_bot.storage.database import Database
from humanoid_bot.storage.models import AuditLog


class AuditTrail:
    def __init__(self, database: Database) -> None:
        self.db = database

    def record(
        self,
        tool: str,
        decision: str,
        risk: str = "low",
        arguments_summary: str = "",
        result: str = "",
    ) -> int:
        return self.db.add_audit(
            tool, decision, risk=risk, arguments_summary=arguments_summary, result=result
        )

    def recent(self, limit: int = 100) -> list[AuditLog]:
        return self.db.recent_audit(limit)
