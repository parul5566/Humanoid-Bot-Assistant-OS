# Phase 7 — Screen Vision & OCR

## Goal
Opt-in screen understanding: capture → OCR → optional vision-model analysis → structured answer. Never auto-executes anything read from screen.

## Files
- `humanoid_bot/vision/screen_capture.py` — capture full screen or window; images released after use
- `humanoid_bot/vision/ocr.py` — pluggable OCR (Windows OCR / Tesseract / EasyOCR; tesseract used in CI)
- `humanoid_bot/vision/vision_analyzer.py` — sends screenshot to vision-capable LLM provider when configured; returns structured description (visible text, UI elements, layout)
- `humanoid_bot/tools/screen_tools.py` — `whats_on_my_screen`, `read_screen_text`, `find_ui_element` tools; screen access permission gate

## Acceptance Criteria
- [ ] "What's on my screen?" captures a screenshot and returns a description (vision provider) or OCR text fallback
- [ ] "Read the text on my screen" returns extracted text
- [ ] First screen-access request asks permission; declining blocks the tool; permission remembered in settings
- [ ] Screenshot data is not persisted beyond the request unless user opts in
- [ ] OCR test passes on a fixture image in CI
