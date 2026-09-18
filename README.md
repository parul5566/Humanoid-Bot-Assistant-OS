# Humanoid Bot Assistant OS

An AI assistant **layer** for Windows 11 — voice, vision, avatar, and controlled
PC automation. Python 3.12+, PySide6, SQLite/SQLAlchemy.

## Run (dev)

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m humanoid_bot.app.main
```

## Checks

```bash
.venv/bin/python -m pytest
.venv/bin/mypy humanoid_bot
.venv/bin/ruff check humanoid_bot tests
```

## Security model

LLM output is never executed as shell or Python. Every action flows:
`AI → structured tool call → argument validation → permission manager →
confirmation if risky → safe tool → Windows`. Risk levels: low (auto),
medium (confirm), high (always explicit confirm). All executions and refusals
are written to an audit log. Secrets are only referenced via environment
variable names in config — never stored in config or logs (a redaction filter
guards the logging pipeline).

## Layout

- `humanoid_bot/app` — entry point, config, paths
- `humanoid_bot/storage` — SQLAlchemy models + database facade
- `humanoid_bot/platform` — Windows/Linux backend abstraction
- `humanoid_bot/logging_setup` — structured logging with secret redaction
