# Phase 2 — Assistant UI

## Goal
Main window, chat panel, 2D humanoid avatar with state machine, system tray, shortcuts.

## Files
- `humanoid_bot/ui/main_window.py` — Fluent-inspired dark/light theme, rounded cards, transparency
- `humanoid_bot/ui/chat/chat_panel.py` — message list, input bar with mic button
- `humanoid_bot/ui/avatar/` — `avatar_widget.py` (2D animated avatar: breathing idle, Listening/Thinking/Speaking/Working/Error states + captions), `avatar_state.py` state machine; architecture ready for future 3D model
- `humanoid_bot/ui/system_tray/tray.py` — Open Assistant / Voice Mode / Pause / Settings / View Logs / Exit
- `humanoid_bot/ui/shortcuts.py` — Ctrl+Space activate, Ctrl+Shift+V voice mode, configurable

## Acceptance Criteria
- [ ] App opens a window with the avatar centered saying "How can I help?"
- [ ] Typing a message adds it to chat and the avatar shows Thinking then Speaking
- [ ] Avatar states visibly change (idle ↔ listening ↔ thinking ↔ speaking ↔ error)
- [ ] Tray icon present with all six menu entries working; Pause actually pauses
- [ ] Ctrl+Space and Ctrl+Shift+V activate the assistant / voice mode
- [ ] Theme switch light/dark works
