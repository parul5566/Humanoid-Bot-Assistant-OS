# Phase 1 — Foundation

## Goal
Project skeleton, typed config, structured logging, SQLite storage layer, dependency management. Everything importable and testable on Linux; Windows-specific parts stubbed behind interfaces.

## Files
- `pyproject.toml` (deps: PySide6, SQLAlchemy, psutil, httpx, pydantic; dev: pytest, mypy, ruff)
- `humanoid_bot/app/main.py`, `config.py` (pydantic-settings, paths under `%APPDATA%/HumanoidBot` on Windows, `~/.local/share` on Linux), `lifecycle.py`
- `humanoid_bot/storage/database.py` (SQLAlchemy engine/session), `models.py` (Setting, TaskHistory, AuditLog, MemoryEntry)
- `humanoid_bot/logging_setup.py` — structured logging, redaction filter (never log keys/passwords/clipboard)
- `humanoid_bot/platform/__init__.py` + `windows_backend.py` / `linux_backend.py` — platform detection
- `tests/` — config, db, logging tests

## Acceptance Criteria (running app)
- [ ] `python -m humanoid_bot` starts without error and prints a startup log line
- [ ] SQLite database file is created on first run with all tables
- [ ] `pytest`, `mypy humanoid_bot` (strict), `ruff check` all pass
