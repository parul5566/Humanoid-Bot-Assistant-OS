import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from pydantic import ValidationError

from humanoid_bot.app.config import PrivacyConfig
from humanoid_bot.security.audit import AuditTrail
from humanoid_bot.security.permissions import PermissionManager
from humanoid_bot.storage.database import Database
from tests.fakes import make_registry


def test_capability_toggle_blocks_file_tools() -> None:
    pm = PermissionManager(PrivacyConfig(allow_file_access=False))
    assert pm.permission_check("search_files") is False
    assert pm.permission_check("delete_files") is False
    assert pm.permission_check("open_application") is True  # not capability-gated


def test_screen_and_clipboard_gates() -> None:
    pm = PermissionManager(PrivacyConfig(allow_screen_access=False,
                                         allow_clipboard=False))
    assert pm.permission_check("read_screen_text") is False
    assert pm.permission_check("whats_on_my_screen") is False
    assert pm.permission_check("read_clipboard") is False
    assert pm.permission_check("type_text") is True


def test_no_confirmer_means_refuse_risky_actions() -> None:
    pm = PermissionManager(PrivacyConfig())
    assert pm.confirm("delete_files", "high", "paths=[]") is False


def test_permissions_persist_and_reload() -> None:
    db = Database.open(":memory:")
    pm = PermissionManager(PrivacyConfig(allow_screen_access=True), db)
    pm.persist()
    reloaded = PermissionManager.load(db)
    assert reloaded.privacy.allow_screen_access is True
    assert reloaded.privacy.allow_clipboard is True  # default for other fields


def test_registry_integrated_with_permission_manager() -> None:
    db = Database.open(":memory:")
    pm = PermissionManager(PrivacyConfig(allow_file_access=False), db)
    registry, _log = make_registry()
    registry.permission_check = pm.permission_check
    registry.confirm = pm.confirm
    audit = AuditTrail(db)
    registry.audit = lambda *a: audit.record(*a)

    result = registry.execute("delete_files", {"paths": ["a"]})
    assert result["ok"] is False
    assert "disabled" in result["summary"]
    entries = audit.recent(5)
    assert entries[-1].decision == "refused"


def test_full_risky_flow_is_audited_end_to_end() -> None:
    db = Database.open(":memory:")
    confirmed: list[tuple[str, str]] = []

    def fake_dialog(tool: str, risk: str, summary: str) -> bool:
        confirmed.append((tool, risk))
        return True

    pm = PermissionManager(PrivacyConfig(), db, confirmer=fake_dialog)
    registry, log = make_registry()
    registry.permission_check = pm.permission_check
    registry.confirm = pm.confirm
    audit = AuditTrail(db)
    registry.audit = lambda *a: audit.record(*a)

    result = registry.execute("delete_files", {"paths": ["a.txt", "b.txt"]})
    assert result["ok"] is True
    assert confirmed == [("delete_files", "high")]
    assert log == ["delete:2"]
    decisions = [e.decision for e in audit.recent(10)]
    assert "executed" in decisions


def test_refusal_recorded_when_cancelled() -> None:
    db = Database.open(":memory:")

    def refuse(_tool: str, _risk: str, _summary: str) -> bool:
        return False

    pm = PermissionManager(PrivacyConfig(), db, confirmer=refuse)
    registry, log = make_registry()
    registry.permission_check = pm.permission_check
    registry.confirm = pm.confirm
    audit = AuditTrail(db)
    registry.audit = lambda *a: audit.record(*a)

    result = registry.execute("close_application", {"application": "x"})
    assert result["ok"] is False
    assert "cancelled" in result["summary"].lower()
    decisions = [e.decision for e in audit.recent(10)]
    assert "cancelled" in decisions


def test_privacy_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        PrivacyConfig.model_validate({"allow_root": True})
