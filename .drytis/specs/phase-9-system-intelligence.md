# Phase 9 — System Intelligence, Clipboard, Notifications, Settings, History

## Goal
System monitoring dashboard, PC commands, clipboard & text assistants, memory UI, notifications, full settings, task history.

## Files
- `humanoid_bot/tools/system_tools.py` — CPU/RAM/disk/network/battery via psutil; commands: lock PC, volume, screenshot, open task manager (risky ones gated)
- `humanoid_bot/ui/system_monitor.py` — live dashboard panel (CPU 23% / RAM 48% / DISK / GPU / BATTERY / NETWORK)
- `humanoid_bot/tools/clipboard_tools.py` — read/write/clear/summarize/translate/rewrite; access always announced in chat
- `humanoid_bot/ai/text_assistant.py` — transform-copied-text flows (professional rewrite, grammar, explain code)
- `humanoid_bot/tools/notification_tools.py` — Windows toast notifications (fallback: tray balloon)
- `humanoid_bot/ui/settings/` — tabs: General (start with Windows, tray, always-on-top, language), Voice, AI (provider/model/temp/limits), Privacy (all capability toggles, memory view/clear), Appearance
- `humanoid_bot/ui/history.py` — task history panel (time, action), view/repeat/delete
- Web search tool (`web_tools.py`) — distinguish search vs open-URL vs read-page; optional
- Memory: short-term + preferences + task history + consent-gated long-term with view/disable/clear

## Acceptance Criteria
- [ ] "How is my PC performing?" returns live CPU/RAM numbers matching the dashboard
- [ ] Dashboard shows live CPU/RAM/disk/battery/network values updating periodically
- [ ] "Summarize what I just copied" reads the clipboard, announces it, and returns a summary
- [ ] "Rewrite this professionally" works on copied text via the AI provider
- [ ] Lock PC / volume change / screenshot commands work; system-config changes gated by confirmation
- [ ] Notifications appear for completed long tasks
- [ ] Settings tabs all functional; privacy toggles take effect immediately
- [ ] History panel lists today's actions with working repeat/delete
- [ ] Memory can be viewed, disabled, and cleared from settings
