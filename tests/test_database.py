from pathlib import Path

from humanoid_bot.storage.database import Database


def test_db_creates_tables(tmp_path: Path) -> None:
    db = Database.open(tmp_path / "test.db")
    tasks = db.recent_tasks()
    assert tasks == []
    assert db.recent_audit() == []


def test_task_history_roundtrip(tmp_path: Path) -> None:
    db = Database.open(tmp_path / "test.db")
    task_id = db.add_task("Opened VS Code", detail="tool=open_application")
    tasks = db.recent_tasks()
    assert len(tasks) == 1
    assert tasks[0].id == task_id
    assert tasks[0].summary == "Opened VS Code"
    db.delete_task(task_id)
    assert db.recent_tasks() == []


def test_audit_roundtrip(tmp_path: Path) -> None:
    db = Database.open(tmp_path / "test.db")
    db.add_audit("open_application", "executed", risk="low", arguments_summary="app=notepad")
    rows = db.recent_audit()
    assert len(rows) == 1
    assert rows[0].decision == "executed"
