"""Memory system: short-term conversation, preferences, task history,
consent-gated long-term memory. Persisted via SQLAlchemy MemoryEntry."""

from __future__ import annotations

from sqlalchemy import delete, select

from humanoid_bot.storage.database import Database
from humanoid_bot.storage.models import MemoryEntry


class Memory:
    """Conversation + long-term memory with explicit user control."""

    def __init__(self, database: Database, long_term_enabled: bool = False) -> None:
        self.db = database
        self.long_term_enabled = long_term_enabled
        # Short-term conversation lives in-process only.
        self.short_term: list[tuple[str, str]] = []  # (role, content)

    # -- short term ----------------------------------------------------
    def remember_turn(self, role: str, content: str) -> None:
        self.short_term.append((role, content))

    def conversation(self, limit: int = 20) -> list[tuple[str, str]]:
        return self.short_term[-limit:]

    def clear_short_term(self) -> None:
        self.short_term.clear()

    # -- long term -----------------------------------------------------
    def store_long_term(self, content: str) -> bool:
        """Store only when long-term memory is explicitly enabled."""
        if not self.long_term_enabled:
            return False
        with self.db.session() as session:
            session.add(MemoryEntry(kind="long_term", content=content))
        return True

    def store_preference(self, content: str) -> None:
        with self.db.session() as session:
            session.add(MemoryEntry(kind="preference", content=content))

    def entries(self, kind: str | None = None) -> list[MemoryEntry]:
        with self.db.session() as session:
            stmt = select(MemoryEntry).order_by(MemoryEntry.created_at.desc())
            if kind:
                stmt = stmt.where(MemoryEntry.kind == kind)
            return list(session.scalars(stmt))

    def clear(self, kind: str | None = None) -> None:
        with self.db.session() as session:
            if kind:
                session.execute(delete(MemoryEntry).where(MemoryEntry.kind == kind))
            else:
                session.execute(delete(MemoryEntry))
