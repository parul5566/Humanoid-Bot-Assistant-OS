"""Settings dialog: General / Voice / AI / Privacy / Appearance tabs."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from humanoid_bot.app.config import AppConfig
from humanoid_bot.security.permissions import PermissionManager


class SettingsDialog(QDialog):
    """Edits an AppConfig in place; caller persists on accept()."""

    def __init__(
        self,
        config: AppConfig,
        permissions: PermissionManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.permissions = permissions
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)

        tabs = QTabWidget()
        tabs.addTab(self._general_tab(), "General")
        tabs.addTab(self._voice_tab(), "Voice")
        tabs.addTab(self._ai_tab(), "AI")
        tabs.addTab(self._privacy_tab(), "Privacy")
        tabs.addTab(self._appearance_tab(), "Appearance")

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    def _general_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.start_with_windows = QCheckBox("Start with Windows")
        self.start_with_windows.setChecked(self.config.general.start_with_windows)
        self.always_on_top = QCheckBox("Always on top")
        self.always_on_top.setChecked(self.config.general.always_on_top)
        self.language = QComboBox()
        self.language.addItems(["en", "de", "hi"])
        self.language.setCurrentText(self.config.general.language)
        form.addRow(self.start_with_windows)
        form.addRow(self.always_on_top)
        form.addRow("Language", self.language)
        return widget

    def _voice_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.stt_backend = QComboBox()
        self.stt_backend.addItems(["fake", "local", "cloud"])
        self.stt_backend.setCurrentText(self.config.voice.stt_backend)
        self.tts_backend = QComboBox()
        self.tts_backend.addItems(["fake", "local"])
        self.tts_backend.setCurrentText(self.config.voice.tts_backend)
        self.wake_word = QCheckBox("Wake word ('hey bot')")
        self.wake_word.setChecked(self.config.voice.wake_word_enabled)
        self.push_to_talk = QCheckBox("Push to talk")
        self.push_to_talk.setChecked(self.config.voice.push_to_talk)
        form.addRow("Speech-to-text", self.stt_backend)
        form.addRow("Text-to-speech", self.tts_backend)
        form.addRow(self.wake_word)
        form.addRow(self.push_to_talk)
        return widget

    def _ai_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.provider = QComboBox()
        self.provider.addItems(["openai", "ollama", "gemini", "fake"])
        self.provider.setCurrentText(self.config.ai.provider)
        self.model = QLabel(self.config.ai.model)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(self.config.ai.temperature)
        form.addRow("Provider", self.provider)
        form.addRow("Model", self.model)
        form.addRow("Temperature", self.temperature)
        return widget

    def _privacy_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        privacy = self.permissions.privacy
        self.allow_screen = QCheckBox("Screen access")
        self.allow_screen.setChecked(privacy.allow_screen_access)
        self.allow_mic = QCheckBox("Microphone access")
        self.allow_mic.setChecked(privacy.allow_microphone)
        self.allow_clipboard = QCheckBox("Clipboard access")
        self.allow_clipboard.setChecked(privacy.allow_clipboard)
        self.allow_files = QCheckBox("File access")
        self.allow_files.setChecked(privacy.allow_file_access)
        self.allow_memory = QCheckBox("Long-term memory")
        self.allow_memory.setChecked(privacy.long_term_memory)
        for box in (self.allow_screen, self.allow_mic, self.allow_clipboard,
                    self.allow_files, self.allow_memory):
            form.addRow(box)
        return widget

    def _appearance_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.theme = QComboBox()
        self.theme.addItems(["dark", "light", "system"])
        self.theme.setCurrentText(self.config.general.theme)
        form.addRow("Theme", self.theme)
        return widget

    # ------------------------------------------------------------------
    def _apply(self) -> None:
        self.config.general.start_with_windows = self.start_with_windows.isChecked()
        self.config.general.always_on_top = self.always_on_top.isChecked()
        self.config.general.language = self.language.currentText()
        self.config.general.theme = self.theme.currentText()  # type: ignore[assignment]
        self.config.voice.stt_backend = self.stt_backend.currentText()  # type: ignore[assignment]
        self.config.voice.tts_backend = self.tts_backend.currentText()  # type: ignore[assignment]
        self.config.voice.wake_word_enabled = self.wake_word.isChecked()
        self.config.voice.push_to_talk = self.push_to_talk.isChecked()
        self.config.ai.provider = self.provider.currentText()  # type: ignore[assignment]
        self.config.ai.temperature = self.temperature.value()
        privacy = self.permissions.privacy
        privacy.allow_screen_access = self.allow_screen.isChecked()
        privacy.allow_microphone = self.allow_mic.isChecked()
        privacy.allow_clipboard = self.allow_clipboard.isChecked()
        privacy.allow_file_access = self.allow_files.isChecked()
        privacy.long_term_memory = self.allow_memory.isChecked()
        self.permissions.persist()
        self.accept()
