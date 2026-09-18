"""OCR abstraction: tesseract in dev/CI, Windows OCR on target platform."""

from __future__ import annotations


class OcrEngine:
    def extract_text(self, png: bytes) -> str:
        raise NotImplementedError


class FakeOcrEngine(OcrEngine):
    def __init__(self, text: str = "Fake OCR output") -> None:
        self.text = text

    def extract_text(self, png: bytes) -> str:
        return self.text


class TesseractOcr(OcrEngine):
    def extract_text(self, png: bytes) -> str:
        import io

        import pytesseract  # type: ignore[import-untyped]
        from PIL import Image

        image = Image.open(io.BytesIO(png))
        return str(pytesseract.image_to_string(image)).strip()


class WindowsOcr(OcrEngine):
    """Windows.Media.Ocr via winsdk; falls back to tesseract."""

    def extract_text(self, png: bytes) -> str:
        try:
            return self._windows_ocr(png)
        except Exception:
            return TesseractOcr().extract_text(png)

    def _windows_ocr(self, png: bytes) -> str:
        import asyncio

        async def _run() -> str:
            from winsdk.windows.graphics.imaging import (  # type: ignore[import-not-found]
                BitmapDecoder,
            )
            from winsdk.windows.media.ocr import (  # type: ignore[import-not-found]
                OcrEngine as WinOcr,
            )
            from winsdk.windows.storage.streams import (  # type: ignore[import-not-found]
                InMemoryRandomAccessStream,
            )

            stream = InMemoryRandomAccessStream()
            await stream.write_async(png)
            decoder = await BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            engine = WinOcr.try_create_from_user_profile_languages()
            if engine is None:
                return ""
            result = await engine.recognize_async(bitmap)
            return "\n".join(line.text for line in result.lines)

        return asyncio.run(_run())
