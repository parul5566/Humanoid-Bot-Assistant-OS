"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from humanoid_bot.app.paths import database_path
from humanoid_bot.storage.models import AuditLog, Base, TaskHistory


def create_db_engine(db_path: Path | None = None) -> Engine:
    url = f"sqlite:///{db_path or database_path()}"
    return create_engine(url, echo=False, future=True)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


class Database:
    """Small facade the rest of the app talks to."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @classmethod
    def open(cls, db_path: Path | None = None) -> Database:
        engine = create_db_engine(db_path)
        init_db(engine)
        return cls(engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self._session_factory() as session:
            yield session
            session.commit()

    # --- Task history -------------------------------------------------
    def add_task(self, summary: str, detail: str = "", status: str = "success") -> int:
        with self.session() as s:
            row = TaskHistory(summary=summary, detail=detail, status=status)
            s.add(row)
            s.flush()
            return int(row.id)

    def recent_tasks(self, limit: int = 50) -> list[TaskHistory]:
        with self.session() as s:
            stmt = select(TaskHistory).order_by(TaskHistory.created_at.desc()).limit(limit)
            return list(s.scalars(stmt))

    def delete_task(self, task_id: int) -> None:
        with self.session() as s:
            row = s.get(TaskHistory, task_id)
            if row:
                s.delete(row)

    # --- Audit log ----------------------------------------------------
    def add_audit(
        self,
        tool: str,
        decision: str,
        risk: str = "low",
        arguments_summary: str = "",
        result: str = "",
    ) -> int:
        with self.session() as s:
            row = AuditLog(
                tool=tool,
                decision=decision,
                risk=risk,
                arguments_summary=arguments_summary,
                result=result,
            )
            s.add(row)
            s.flush()
            return int(row.id)

    def recent_audit(self, limit: int = 100) -> list[AuditLog]:
        with self.session() as s:
            stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
            return list(s.scalars(stmt))
