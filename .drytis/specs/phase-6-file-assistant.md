# Phase 6 — File Assistant

## Goal
Natural-language file operations via tools; destructive ops always confirmed and target-identified first.

## Files
- `humanoid_bot/tools/file_tools.py` — search_files (glob/date/size filters), open_folder, open_file, create_folder, create_file, move_files, rename_files, delete_files
- Backed by `pathlib` cross-platform; scope limited to a configurable list of allowed roots (Desktop, Documents, Downloads, user folders)
- Error recovery: fuzzy path matching, "did you mean" suggestions

## Acceptance Criteria
- [ ] "Create a folder called Projects on Desktop" creates it
- [ ] "Find PDF files modified this week" returns a readable list in chat
- [ ] Move/rename of multiple files shows count + targets and requires Confirm/Cancel before executing
- [ ] Delete is always High risk: explicit confirmation dialog, exact target list shown
- [ ] Operations outside allowed roots are refused with a clear explanation
- [ ] Each action is written to task history and audit log
