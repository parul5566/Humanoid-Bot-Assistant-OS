"""Animated 2D humanoid avatar widget."""

from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from humanoid_bot.ui.avatar.avatar_state import STATE_CAPTIONS, AvatarState


class AvatarWidget(QWidget):
    """Lightweight 2D humanoid avatar.

    A stylized humanoid bust (head + shoulders) with an animated chest glow
    (breathing) and a pulsing ring whose color/behavior depends on the state.
    The widget API (set_state) is deliberately simple so a future 3D model
    can replace the paint implementation without touching callers.
    """

    STATE_COLORS: dict[AvatarState, tuple[int, int, int]] = {
        AvatarState.IDLE: (90, 160, 255),
        AvatarState.LISTENING: (80, 220, 120),
        AvatarState.THINKING: (255, 190, 70),
        AvatarState.SPEAKING: (140, 120, 255),
        AvatarState.WORKING: (70, 200, 220),
        AvatarState.ERROR: (240, 80, 90),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = AvatarState.IDLE
        self._phase = 0.0
        self.setMinimumSize(260, 300)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)  # ~30 fps

        self._caption = QLabel(STATE_CAPTIONS[AvatarState.IDLE], self)
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(self._caption)
        layout.addStretch(1)

    # ------------------------------------------------------------------
    def set_state(self, state: AvatarState, caption: str | None = None) -> None:
        self._state = state
        self._caption.setText(caption or STATE_CAPTIONS[state])

    def state(self) -> AvatarState:
        return self._state

    def _tick(self) -> None:
        self._phase = (self._phase + 0.05) % (2 * math.pi)
        self.update()

    # ------------------------------------------------------------------
    def paintEvent(self, event: object) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx = w / 2
        color = QColor(*self.STATE_COLORS[self._state])

        # Breathing factor: subtle scale oscillation while idle.
        breathing = 1.0 + (math.sin(self._phase) * 0.02)

        # Chest glow (radial gradient orb) behind the figure.
        glow_r = min(w, h) * 0.42 * breathing
        gradient = QRadialGradient(cx, h * 0.42, glow_r)
        glow = QColor(color)
        glow.setAlpha(90 if self._state != AvatarState.IDLE else 55)
        gradient.setColorAt(0.0, glow)
        fade = QColor(color)
        fade.setAlpha(0)
        gradient.setColorAt(1.0, fade)
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QRectF(cx - glow_r, h * 0.42 - glow_r, glow_r * 2, glow_r * 2)
        )

        # Head.
        head_r = min(w, h) * 0.13 * breathing
        head_cy = h * 0.30
        painter.setBrush(QColor(30, 34, 46))
        painter.setPen(QPen(color, 3))
        painter.drawEllipse(QRectF(cx - head_r, head_cy - head_r, head_r * 2, head_r * 2))

        # Eyes.
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        eye_r = head_r * 0.14
        if self._state is AvatarState.LISTENING:
            eye_r *= 1.0 + 0.3 * abs(math.sin(self._phase * 2))
        eye_dx = head_r * 0.38
        for sign in (-1, 1):
            painter.drawEllipse(
                QRectF(
                    cx + sign * eye_dx - eye_r,
                    head_cy - head_r * 0.15 - eye_r,
                    eye_r * 2,
                    eye_r * 2,
                )
            )

        # Mouth: animates while speaking, thin line otherwise.
        painter.setPen(QPen(color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if self._state is AvatarState.SPEAKING:
            mouth_open = abs(math.sin(self._phase * 3)) * head_r * 0.35
            painter.drawLine(
                int(cx - head_r * 0.35),
                int(head_cy + head_r * 0.45),
                int(cx + head_r * 0.35),
                int(head_cy + head_r * 0.45 + mouth_open),
            )
        else:
            painter.drawLine(
                int(cx - head_r * 0.3),
                int(head_cy + head_r * 0.5),
                int(cx + head_r * 0.3),
                int(head_cy + head_r * 0.5),
            )

        # Shoulders.
        painter.setBrush(QColor(30, 34, 46))
        painter.setPen(QPen(color, 3))
        shoulder_w = min(w, h) * 0.46 * breathing
        painter.drawRoundedRect(
            QRectF(cx - shoulder_w / 2, h * 0.52, shoulder_w, h * 0.34),
            shoulder_w / 2.2,
            shoulder_w / 2.2,
        )

        # Status ring pulse for active states.
        if self._state in (AvatarState.LISTENING, AvatarState.THINKING, AvatarState.WORKING):
            pulse = (math.sin(self._phase * 2) + 1) / 2
            ring = QColor(color)
            ring.setAlpha(int(40 + 70 * pulse))
            pen = QPen(ring, 4)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            ring_r = min(w, h) * (0.5 + 0.04 * pulse)
            painter.drawEllipse(QRectF(cx - ring_r, h * 0.42 - ring_r, ring_r * 2, ring_r * 2))
