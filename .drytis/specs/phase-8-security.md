# Phase 8 — Security: Permissions, Confirmation, Audit

## Goal
Central permission manager enforcing the pipeline: structured tool call → validation → risk classification → confirmation → execution → audit log. No LLM→shell path ever.

## Files
- `humanoid_bot/security/permissions.py` — per-tool + per-capability permissions (screen, mic, clipboard, files, memory), persisted settings
- `humanoid_bot/security/confirmation.py` — Confirm/Cancel dialog used by medium/high risk tools, showing exact targets and counts
- `humanoid_bot/security/audit.py` — append-only audit log (timestamp, tool, arguments-summary, risk, decision, result) in SQLite; viewable in UI
- Risk policy table in tool registry: low = auto (open app, read system info, search), medium = confirm (move/rename files, close apps, modify settings), high = always explicit confirm (delete, run unknown program, admin/system config, install)
- Integration: permission check enforced inside tool registry `execute()` — impossible to bypass

## Acceptance Criteria
- [ ] High-risk tool invoked by the AI always shows a confirmation dialog; Cancel aborts safely with a logged refusal
- [ ] Low-risk tools execute without prompting
- [ ] Disabling a capability permission (e.g. clipboard) makes those tools refuse even if the AI requests them
- [ ] Audit log records every tool execution and refusal, viewable from settings
- [ ] A deliberate attempt to call a nonexistent tool or pass invalid args is blocked and logged
