"""Screen capture abstraction.

RealScreenCapture uses mss on Windows; FakeScreenCapture returns a fixture
image so vision tests run headless. Images are produced as PNG bytes and
never persisted beyond the request.
"""

from __future__ import annotations

import io


def encode_png(width: int, height: int, rgba: bytes) -> bytes:
    """Encode raw RGBA into PNG bytes via Pillow (lazy import)."""
    from PIL import Image

    image = Image.frombytes("RGBA", (width, height), rgba)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def decode_png(png: bytes) -> tuple[int, int, bytes]:
    from PIL import Image

    image = Image.open(io.BytesIO(png)).convert("RGBA")
    return image.width, image.height, image.tobytes()


class ScreenCapture:
    """Returns PNG bytes of the requested screen region."""

    def capture(self, monitor: int = 1) -> bytes:
        raise NotImplementedError


class FakeScreenCapture(ScreenCapture):
    """Returns a synthetic image (solid background + noise pattern)."""

    def __init__(self, width: int = 640, height: int = 400, label: str = "fake") -> None:
        self.width = width
        self.height = height
        self.label = label

    def capture(self, monitor: int = 1) -> bytes:
        row = bytearray()
        seed = sum(self.label.encode()) % 251
        for y in range(self.height):
            for x in range(self.width):
                value = (x * y + seed) % 256
                row += bytes((value, value, value, 255))
        return encode_png(self.width, self.height, bytes(row))


class RealScreenCapture(ScreenCapture):
    def capture(self, monitor: int = 1) -> bytes:
        import mss  # type: ignore[import-not-found]
        import mss.tools  # type: ignore[import-not-found]

        with mss.mss() as scanner:
            shot = scanner.grab(scanner.monitors[monitor])
            return bytes(mss.tools.to_png(shot.rgb, shot.size))
