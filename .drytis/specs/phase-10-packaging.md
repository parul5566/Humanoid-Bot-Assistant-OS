# Phase 10 — Packaging & Hardening

## Goal
Windows executable + installer assets, performance hardening, test/type/docs completion. (Built in this Linux container as scripts/specs; the .exe itself is produced by running them on a Windows machine.)

## Files
- `packaging/humanoidbot.spec` — PyInstaller spec (one-dir windowed app, assets bundled, name `HumanoidBotAssistant.exe`)
- `packaging/installer.iss` — Inno Setup script: installer, desktop + Start Menu shortcuts, uninstaller, auto-start-with-Windows option
- `packaging/README.md` — exact Windows build steps
- Performance: async/worker-thread usage audit, idle CPU near-zero (event-driven voice loop), screenshot/memory release, startup < few seconds
- Final pass: full pytest suite green, mypy strict clean, ruff clean, README (features, security model, build instructions)

## Acceptance Criteria
- [ ] `pytest`, `mypy`, `ruff` all pass on the full codebase
- [ ] App idles at negligible CPU (event-driven, no polling loops)
- [ ] Long operations run on background workers; UI stays responsive during a multi-step task
- [ ] PyInstaller spec + Inno Setup script present and documented; build succeeds when run on Windows
- [ ] README documents the security model and how to add apps to the registry
