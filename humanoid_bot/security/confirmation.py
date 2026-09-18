"""Qt confirmation dialog for medium/high risk actions."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QMessageBox, QWidget

ConfirmCallback = Callable[[str, str, str], bool]

RISK_EXPLANATIONS = {
    "medium": "This action may be hard to undo.",
    "high": "This action is potentially destructive or irreversible.",
}


class ConfirmationDialog:
    """Modal Confirm/Cancel dialog showing exact tool + targets."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self.parent = parent

    def ask(self, tool_name: str, risk: str, summary: str) -> bool:
        explanation = RISK_EXPLANATIONS.get(risk, "")
        box = QMessageBox(self.parent)
        box.setIcon(
            QMessageBox.Icon.Warning if risk == "high" else QMessageBox.Icon.Question
        )
        box.setWindowTitle(f"Confirm {risk}-risk action")
        box.setText(f"The assistant wants to run: {tool_name}")
        box.setInformativeText(f"{explanation}\n\n{summary}")
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        return box.exec() == QMessageBox.StandardButton.Yes


def make_confirm_callback(dialog: ConfirmationDialog) -> ConfirmCallback:
    def _confirm(tool_name: str, risk: str, summary: str) -> bool:
        return dialog.ask(tool_name, risk, summary)

    return _confirm
