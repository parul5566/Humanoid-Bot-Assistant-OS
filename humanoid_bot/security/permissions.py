"""Permission manager: per-tool + capability permissions with persistence."""

from __future__ import annotations

from collections.abc import Callable

from humanoid_bot.app.config import PrivacyConfig
from humanoid_bot.storage.database import Database
from humanoid_bot.storage.models import Setting

# tool name prefix -> capability toggle in PrivacyConfig
CAPABILITY_RULES: list[tuple[str, str]] = [
    ("search_files", "allow_file_access"),
    ("open_path", "allow_file_access"),
    ("create_folder", "allow_file_access"),
    ("create_file", "allow_file_access"),
    ("move_files", "allow_file_access"),
    ("rename_files", "allow_file_access"),
    ("delete_files", "allow_file_access"),
    ("whats_on_my_screen", "allow_screen_access"),
    ("read_screen_text", "allow_screen_access"),
    ("read_clipboard", "allow_clipboard"),
    ("write_clipboard", "allow_clipboard"),
    ("start_listening", "allow_microphone"),
]

SETTING_KEY = "privacy_config"

ConfirmCallback = Callable[[str, str, str], bool]


class PermissionManager:
    """Decides whether a tool may run and whether confirmation is needed."""

    def __init__(
        self,
        privacy: PrivacyConfig,
        database: Database | None = None,
        confirmer: ConfirmCallback | None = None,
    ) -> None:
        self.privacy = privacy
        self.db = database
        self.confirmer = confirmer

    # ------------------------------------------------------------------
    def permission_check(self, tool_name: str) -> bool:
        for prefix, attr in CAPABILITY_RULES:
            if tool_name.startswith(prefix):
                return bool(getattr(self.privacy, attr, True))
        return True

    def confirm(self, tool_name: str, risk: str, summary: str) -> bool:
        if self.confirmer is None:
            # Headless/no-UI fallback: refuse risky actions rather than
            # silently executing them.
            return False
        return self.confirmer(tool_name, risk, summary)

    # ------------------------------------------------------------------
    def persist(self) -> None:
        if self.db is None:
            return
        with self.db.session() as session:
            existing = session.get(Setting, SETTING_KEY)
            value = self.privacy.model_dump_json()
            if existing:
                existing.value = value
            else:
                session.add(Setting(key=SETTING_KEY, value=value))

    @classmethod
    def load(
        cls, database: Database, confirmer: ConfirmCallback | None = None
    ) -> PermissionManager:
        privacy = PrivacyConfig()
        with database.session() as session:
            stored = session.get(Setting, SETTING_KEY)
            if stored:
                privacy = PrivacyConfig.model_validate_json(stored.value)
        return cls(privacy, database, confirmer)
