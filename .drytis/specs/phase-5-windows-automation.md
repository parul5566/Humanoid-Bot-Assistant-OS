# Phase 5 — Windows Automation Engine

## Goal
Safe, typed PC-control operations behind a tool-facing API; app registry; keyboard/mouse/window control. Windows backends (pywinauto/pyautogui/subprocess/psutil) with Linux fakes for tests.

## Files
- `humanoid_bot/automation/applications.py` + `humanoid_bot/automation/app_registry.py` — app registry (name, executable, args, launch method), configurable via settings; known apps (chrome, notepad, calculator, code, task manager)
- `humanoid_bot/automation/windows.py` — `open_application`, `close_application`, `find_window`, `get_active_window`, `read_window`
- `humanoid_bot/automation/keyboard.py` — `type_text`, `press_key`, `hotkey`
- `humanoid_bot/automation/mouse.py` — `click`, `move_mouse`
- `humanoid_bot/automation/browser.py` — Playwright-based module (open URL, navigate, click, type, extract text, screenshot); sensitive sites/actions require confirmation
- `humanoid_bot/tools/app_tools.py`, `keyboard_tools.py`, `mouse_tools.py`, `browser_tools.py` — registry-registered tools with risk levels

## Acceptance Criteria
- [ ] "Open Notepad" / "Launch Calculator" / "Close Calculator" commands work via tool calls (real on Windows, fake backend verified in tests)
- [ ] Unknown application triggers the error-recovery flow: "I couldn't find X — search installed location?"
- [ ] Keyboard/mouse tools perform typed operations with bounds validation (no raw code execution)
- [ ] Browser tool can open a URL and extract visible text (Playwright test in CI)
- [ ] All automation tools appear in the tool registry with correct risk levels
