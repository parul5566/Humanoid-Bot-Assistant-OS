"""File assistant tools: search/open/create/move/rename/delete.

Security invariants:
- All paths must resolve inside an allowed root (configurable; defaults to
  the user's profile folders).
- move/rename of multiple files = medium risk; delete = high risk.
- Exact target lists are included in the result summaries so confirmation
  dialogs can show them.
"""

from __future__ import annotations

import fnmatch
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from pydantic import BaseModel, Field

from humanoid_bot.tools.registry import Risk, ToolDefinition, ToolRegistry
from humanoid_bot.tools.results import ToolResult


class FileScope:
    """Allowed-roots guard."""

    def __init__(self, roots: list[Path]) -> None:
        self.roots = [root.resolve() for root in roots]

    def contains(self, path: Path) -> bool:
        try:
            resolved = path.resolve()
        except OSError:
            return False
        return any(resolved == root or root in resolved.parents for root in self.roots)

    def check(self, path: Path) -> str | None:
        """Return an error message if the path is outside scope, else None."""
        if not self.contains(path):
            return (
                f"'{path}' is outside the allowed folders "
                f"({', '.join(str(r) for r in self.roots)})."
            )
        return None


class SearchFilesArgs(BaseModel):
    pattern: str = Field(description="Glob pattern, e.g. '*.pdf'")
    root: str = Field(description="Folder to search in")
    modified_within_days: int | None = Field(default=None, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class OpenPathArgs(BaseModel):
    path: str


class CreateFolderArgs(BaseModel):
    path: str
    name: str = Field(min_length=1, max_length=120)


class CreateFileArgs(BaseModel):
    path: str
    name: str = Field(min_length=1, max_length=120)
    content: str = Field(default="", max_length=100000)


class MoveFilesArgs(BaseModel):
    paths: list[str] = Field(min_length=1)
    destination: str


class RenameFilesArgs(BaseModel):
    paths: list[str] = Field(min_length=1)
    new_names: list[str] = Field(min_length=1)


class DeleteFilesArgs(BaseModel):
    paths: list[str] = Field(min_length=1)


def register_file_tools(
    registry: ToolRegistry,
    scope: FileScope,
    open_handler: object | None = None,
) -> None:
    """open_handler: callable(path) - platform open (explorer/xdg-open)."""

    if open_handler is None:
        def default_open(target: str) -> None:
            import subprocess
            import sys

            if sys.platform == "win32":
                subprocess.Popen(["explorer", target])
            else:
                subprocess.Popen(["xdg-open", target])
        open_handler = default_open

    def search_files(args_b: BaseModel) -> ToolResult:
        args = cast(SearchFilesArgs, args_b)
        root = Path(args.root)
        if error := scope.check(root):
            return {"ok": False, "summary": error}
        if not root.is_dir():
            return {"ok": False, "summary": f"'{args.root}' is not a folder."}
        cutoff = None
        if args.modified_within_days is not None:
            cutoff = datetime.now(UTC) - timedelta(days=args.modified_within_days)
        matches: list[str] = []
        for candidate in sorted(root.rglob(args.pattern)):
            if cutoff is not None:
                mtime = datetime.fromtimestamp(candidate.stat().st_mtime, tz=UTC)
                if mtime < cutoff:
                    continue
            matches.append(str(candidate))
            if len(matches) >= args.limit:
                break
        if not matches:
            return {"ok": True, "summary": "No matching files found."}
        listing = "\n".join(matches)
        return {
            "ok": True,
            "summary": f"Found {len(matches)} file(s):",
            "detail": listing,
        }

    def open_path(args_b: BaseModel) -> ToolResult:
        args = cast(OpenPathArgs, args_b)
        path = Path(args.path)
        if error := scope.check(path):
            return {"ok": False, "summary": error}
        if not path.exists():
            return {"ok": False, "summary": f"'{args.path}' does not exist."}
        open_handler(str(path))  # type: ignore[operator]
        kind = "folder" if path.is_dir() else "file"
        return {"ok": True, "summary": f"Opened {kind} {path.name}."}

    def create_folder(args_b: BaseModel) -> ToolResult:
        args = cast(CreateFolderArgs, args_b)
        parent = Path(args.path)
        if error := scope.check(parent):
            return {"ok": False, "summary": error}
        target = parent / args.name
        if error := scope.check(target):
            return {"ok": False, "summary": error}
        if target.exists():
            return {"ok": False, "summary": f"'{target}' already exists."}
        target.mkdir(parents=False)
        return {"ok": True, "summary": f"Created folder {target}."}

    def create_file(args_b: BaseModel) -> ToolResult:
        args = cast(CreateFileArgs, args_b)
        parent = Path(args.path)
        if error := scope.check(parent):
            return {"ok": False, "summary": error}
        target = parent / args.name
        if error := scope.check(target):
            return {"ok": False, "summary": error}
        if target.exists():
            return {"ok": False, "summary": f"'{target}' already exists."}
        target.write_text(args.content, encoding="utf-8")
        return {"ok": True, "summary": f"Created file {target}."}

    def _resolve_existing(paths: list[str]) -> tuple[list[Path], str | None]:
        resolved: list[Path] = []
        for raw in paths:
            path = Path(raw)
            if error := scope.check(path):
                return [], error
            if not path.exists():
                return [], f"'{raw}' does not exist."
            resolved.append(path)
        return resolved, None

    def move_files(args_b: BaseModel) -> ToolResult:
        args = cast(MoveFilesArgs, args_b)
        destination = Path(args.destination)
        if error := scope.check(destination):
            return {"ok": False, "summary": error}
        if not destination.is_dir():
            return {"ok": False, "summary": f"Destination '{args.destination}' is not a folder."}
        sources, error = _resolve_existing(args.paths)
        if error:
            return {"ok": False, "summary": error}
        assert sources is not None
        moved: list[str] = []
        for source in sources:
            target = destination / source.name
            if target.exists():
                moved.append(f"skipped {source.name} (already exists at destination)")
                continue
            source.rename(target)
            moved.append(f"moved {source.name}")
        return {
            "ok": True,
            "summary": f"Moved {len(sources)} item(s) to {destination}: "
            + "; ".join(moved),
        }

    def rename_files(args_b: BaseModel) -> ToolResult:
        args = cast(RenameFilesArgs, args_b)
        if len(args.paths) != len(args.new_names):
            return {"ok": False, "summary": "Number of files and new names must match."}
        sources, error = _resolve_existing(args.paths)
        if error:
            return {"ok": False, "summary": error}
        assert sources is not None
        results: list[str] = []
        for source, new_name in zip(sources, args.new_names, strict=True):
            target = source.with_name(new_name)
            if error := scope.check(target):
                return {"ok": False, "summary": error}
            if target.exists():
                results.append(f"skipped {source.name} (target exists)")
                continue
            source.rename(target)
            results.append(f"{source.name} -> {new_name}")
        return {"ok": True, "summary": "Renamed: " + "; ".join(results)}

    def delete_files(args_b: BaseModel) -> ToolResult:
        args = cast(DeleteFilesArgs, args_b)
        targets, error = _resolve_existing(args.paths)
        if error:
            return {"ok": False, "summary": error}
        assert targets is not None
        names = ", ".join(t.name for t in targets)
        for target in targets:
            if target.is_dir():
                target.rmdir()
            else:
                target.unlink()
        return {"ok": True, "summary": f"Deleted {len(targets)} item(s): {names}"}

    definitions: tuple[ToolDefinition[BaseModel], ...] = (
        ToolDefinition("search_files", "Search files by pattern and optional recency",
                       SearchFilesArgs, search_files, Risk.LOW),
        ToolDefinition("open_path", "Open a file or folder",
                       OpenPathArgs, open_path, Risk.LOW),
        ToolDefinition("create_folder", "Create a new folder",
                       CreateFolderArgs, create_folder, Risk.LOW),
        ToolDefinition("create_file", "Create a new text file",
                       CreateFileArgs, create_file, Risk.LOW),
        ToolDefinition("move_files", "Move files to a destination folder",
                       MoveFilesArgs, move_files, Risk.MEDIUM),
        ToolDefinition("rename_files", "Rename one or more files",
                       RenameFilesArgs, rename_files, Risk.MEDIUM),
        ToolDefinition("delete_files", "Permanently delete files or empty folders",
                       DeleteFilesArgs, delete_files, Risk.HIGH),
    )
    for definition in definitions:
        registry.register(definition)


__all__ = [
    "FileScope",
    "register_file_tools",
    "fnmatch",
    "Path",
    "datetime",
]
