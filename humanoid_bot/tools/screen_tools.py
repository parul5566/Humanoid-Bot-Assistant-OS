"""Screen tools behind the permission gate."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel, Field

from humanoid_bot.tools.registry import Risk, ToolDefinition, ToolRegistry
from humanoid_bot.tools.results import ToolResult
from humanoid_bot.vision.ocr import OcrEngine
from humanoid_bot.vision.screen_capture import ScreenCapture
from humanoid_bot.vision.vision_analyzer import VisionAnalyzer


class ScreenQuestionArgs(BaseModel):
    question: str = Field(default="What is displayed on this screen?",
                          max_length=500)


class ReadScreenTextArgs(BaseModel):
    max_chars: int = Field(default=4000, ge=100, le=20000)


def register_screen_tools(
    registry: ToolRegistry,
    capture: ScreenCapture,
    ocr: OcrEngine,
    analyzer: VisionAnalyzer,
) -> None:
    def _grab() -> bytes | ToolResult:
        png = capture.capture()
        return png

    def whats_on_screen(args_b: BaseModel) -> ToolResult:
        args = cast(ScreenQuestionArgs, args_b)
        grabbed = _grab()
        if isinstance(grabbed, dict):
            return grabbed
        description = analyzer.describe(grabbed, args.question)
        if description is None:
            text = ocr.extract_text(grabbed)
            if not text:
                return {
                    "ok": False,
                    "summary": "No vision provider configured and OCR found no text.",
                }
            return {
                "ok": True,
                "summary": "OCR fallback (no vision provider configured):",
                "detail": text[:4000],
            }
        return {"ok": True, "summary": description}

    def read_screen_text(args_b: BaseModel) -> ToolResult:
        args = cast(ReadScreenTextArgs, args_b)
        grabbed = _grab()
        if isinstance(grabbed, dict):
            return grabbed
        text = ocr.extract_text(grabbed)
        if not text:
            return {"ok": False, "summary": "No readable text found on screen."}
        return {"ok": True, "summary": text[: args.max_chars]}

    definitions: tuple[ToolDefinition[BaseModel], ...] = (
        ToolDefinition("whats_on_my_screen", "Describe what is displayed on screen",
                       ScreenQuestionArgs, whats_on_screen, Risk.LOW),
        ToolDefinition("read_screen_text", "Extract visible text via OCR",
                       ReadScreenTextArgs, read_screen_text, Risk.LOW),
    )
    for definition in definitions:
        registry.register(definition)
