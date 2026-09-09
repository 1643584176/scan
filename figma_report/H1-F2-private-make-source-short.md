# Figma H1 Submission (F2 short) — 2026-09-07

Title: Unauthorized download of private Figma Make source code

Severity: HIGH
Weakness: CWE-862 Missing Authorization
Asset: https://www.figma.com

## Summary
`FileMakeVersionsView` (livegraph WS) returns private MakeVersion records — including `codeSnapshotKey` — for any `fileKey`, anonymously. `GET /api/rev/{file_key}/code_snapshot/{key}` then returns the complete source of that private Make file to any logged-in account. No access to the file is required.

## Steps To Reproduce
Two unrelated accounts: B owns a private Make file with one saved version; A has no relationship to B or the file.

1. Anonymous (no Cookie) WS subscribe: `FileMakeVersionsView {fileKey: B_FILE}` → returns B's MakeVersion with `chatThreadId` + `codeSnapshotKey`. Re-verified 2026-09-07: no auth gate, still works.
2. As A: `GET /api/rev/{B_FILE}/code_snapshot/{leaked_key}` → HTTP 200, full `code_files` incl. unique marker `H1_B_PRIVATE_SOURCE_<random>` planted by B in `src/App.tsx`.
3. Negative control, same A session/file: `GET /api/ai_chat/threads?owner_id={B_FILE}&owner_type=file` → HTTP 403 "You don't have permission to use AI in this file." The normal path denies A this file's data.
4. Binding control: same snapshot key under A's own file key → 404 "Code snapshot not found" (snapshot↔file binding checked; user→file read auth not).

## Impact
Complete confidentiality loss of private Figma Make source code; keys enumerable anonymously; any logged-in account exploits. No victim interaction.

## Root cause
`FileMakeVersionsView`/`code_snapshot` verify the snapshot-file relationship but never the requester's read access to the file. Fix: apply the same file-read authz as the sibling thread-list endpoint (403 case above).
