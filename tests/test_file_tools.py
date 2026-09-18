import os
from pathlib import Path

from humanoid_bot.tools.file_tools import FileScope, register_file_tools
from humanoid_bot.tools.registry import ToolRegistry


def make(tmp_path: Path) -> tuple[ToolRegistry, FileScope]:
    scope = FileScope([tmp_path / "Desktop", tmp_path / "Documents",
                       tmp_path / "Downloads"])
    for root in scope.roots:
        root.mkdir(parents=True, exist_ok=True)
    registry = ToolRegistry()
    opened: list[str] = []
    register_file_tools(registry, scope, open_handler=opened.append)
    registry.opened = opened  # type: ignore[attr-defined]
    return registry, scope


def test_search_finds_files_with_recency_filter(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    docs = tmp_path / "Documents"
    (docs / "report.pdf").write_text("x")
    (docs / "old.pdf").write_text("x")
    old = docs / "old.pdf"
    past = os.path.getmtime(old) - 30 * 86400
    os.utime(old, (past, past))

    result = registry.execute("search_files", {
        "pattern": "*.pdf", "root": str(docs), "modified_within_days": 7,
    })
    assert result["ok"] is True
    assert "report.pdf" in result["detail"]
    assert "old.pdf" not in result["detail"]


def test_search_outside_scope_refused(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    result = registry.execute("search_files", {
        "pattern": "*", "root": str(tmp_path.parent),
    })
    assert result["ok"] is False
    assert "outside the allowed folders" in result["summary"]


def test_create_folder_and_file(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    desktop = str(tmp_path / "Desktop")
    assert registry.execute("create_folder", {
        "path": desktop, "name": "Projects"})["ok"] is True
    assert (tmp_path / "Desktop" / "Projects").is_dir()
    result = registry.execute("create_file", {
        "path": desktop, "name": "notes.txt", "content": "hello"})
    assert result["ok"] is True
    assert (tmp_path / "Desktop" / "notes.txt").read_text() == "hello"
    # duplicates refused
    assert registry.execute("create_folder", {
        "path": desktop, "name": "Projects"})["ok"] is False


def test_open_path(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    downloads = tmp_path / "Downloads"
    result = registry.execute("open_path", {"path": str(downloads)})
    assert result["ok"] is True
    assert registry.opened == [str(downloads)]  # type: ignore[attr-defined]
    assert registry.execute("open_path", {"path": "/etc"})["ok"] is False


def test_move_files_medium_risk_requires_confirmation(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    docs = tmp_path / "Documents"
    src = docs / "a.txt"
    src.write_text("a")
    archive = tmp_path / "Desktop" / "Archive"
    archive.mkdir()
    # cancel
    registry.confirm = lambda *a: False
    result = registry.execute("move_files", {
        "paths": [str(src)], "destination": str(archive)})
    assert result["ok"] is False and src.exists()
    # confirm
    registry.confirm = lambda *a: True
    result = registry.execute("move_files", {
        "paths": [str(src)], "destination": str(archive)})
    assert result["ok"] is True
    assert not src.exists() and (archive / "a.txt").exists()


def test_rename_files(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    docs = tmp_path / "Documents"
    a, b = docs / "a.txt", docs / "b.txt"
    a.write_text("a"), b.write_text("b")
    registry.confirm = lambda *a: True
    result = registry.execute("rename_files", {
        "paths": [str(a), str(b)], "new_names": ["alpha.txt", "beta.txt"]})
    assert result["ok"] is True
    assert (docs / "alpha.txt").exists() and (docs / "beta.txt").exists()


def test_rename_mismatch_counts_refused(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    docs = tmp_path / "Documents"
    result = registry.execute("rename_files", {
        "paths": [str(docs / "a.txt")], "new_names": ["x", "y"]})
    assert result["ok"] is False


def test_delete_is_high_risk_cancel_aborts(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    victim = tmp_path / "Documents" / "victim.txt"
    victim.write_text("data")
    registry.confirm = lambda *a: False
    result = registry.execute("delete_files", {"paths": [str(victim)]})
    assert result["ok"] is False
    assert victim.exists()  # untouched after cancel
    registry.confirm = lambda *a: True
    result = registry.execute("delete_files", {"paths": [str(victim)]})
    assert result["ok"] is True
    assert not victim.exists()


def test_delete_nonexistent_refused(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    registry.confirm = lambda *a: True
    result = registry.execute("delete_files", {
        "paths": [str(tmp_path / "Documents" / "ghost.txt")]})
    assert result["ok"] is False


def test_move_skips_existing_targets(tmp_path: Path) -> None:
    registry, _ = make(tmp_path)
    docs = tmp_path / "Documents"
    src = docs / "dup.txt"
    src.write_text("src")
    dest_dir = tmp_path / "Desktop"
    (dest_dir / "dup.txt").write_text("dest")
    registry.confirm = lambda *a: True
    result = registry.execute("move_files", {
        "paths": [str(src)], "destination": str(dest_dir)})
    assert result["ok"] is True
    assert "skipped" in result["summary"]
    assert src.exists()  # not overwritten
