# Figma H1 Submission (viewer export restriction bypass) — 2026-09-07

> STATUS: 待提交

Title: viewer_export_restricted bypass — full .fig still downloadable via /version/{vid}/canvas

Asset: https://www.figma.com
API: GET /version/{version_id}/canvas?fk={file_key}&fv=1
Severity: MEDIUM
Weakness: CWE-284 Improper Access Control

## Summary
Owner disables "Viewers can copy, share, and export from this file" (Share → Share settings → Advanced). Per help article 360040045574, view-only users (invited or via shared link) must then be unable to "Save a copy of the file to your computer".

The flag IS enforced server-side on the official duplicate endpoint (`POST /api/multiplayer/{fk}/copy` → 403, boot `can_export:false`, UI menus disabled), but the download endpoint `GET /version/{vid}/canvas?fk={fk}&fv=1` skips the check: a signed-in view-only user AND an anonymous visitor still download the complete .fig, md5-identical to the owner's download.

## Steps To Reproduce
Target: `IHt8kgtR3XmtqU5i8vz7p1` (owner A UID 1666382703778278399, public view link). Attacker: B UID 1667396392129259941 (view-only). Video: `2394436713245131286`.

1. Restriction OFF: B's boot = `"can_edit":false,"can_export":true`; duplicate to drafts (`POST /api/multiplayer/IHt8kgtR3XmtqU5i8vz7p1/copy`) → 200; `GET /version/2394436713245131286/canvas?fk=IHt8kgtR3XmtqU5i8vz7p1&fv=1` → 200 (176925 B).
2. Owner enables it:
   ```
   PUT /api/files/IHt8kgtR3XmtqU5i8vz7p1  (A cookie, X-Figma-User-ID 1666382703778278399)
   {"viewer_export_restricted": true}
   ```
   → 200; meta shows `"viewer_export_restricted": true`.
3. Server ENFORCES it for B: boot now `"can_export":false`, same duplicate call → **403** "You do not have permission to duplicate this file."
4. Bypass: B requests the same canvas endpoint → **200**, 176925 B, md5 `afd059d13dab81428c4602290b17caa2` — identical to the owner's own download.
5. Anonymous visitor (no session), restriction ON → **200**, same file.
6. Restriction reverted; state clean except test copy `OUnFP5dVe88aJtlfI6Iy8S` in B's drafts (no REST delete; UI-deletable).

Evidence: `_v65_boot_b_free.html` (`can_export:true`) vs `_v65_boot_b_restricted.html` (`can_export:false`); `_v66_a_owner_dl.fig` + `_v65_b_restricted_dl.fig` (md5-identical).

## Impact
Documented "Viewers can't save a copy" control is ineffective: any view-only user or anonymous link visitor obtains the full .fig source, defeating the owner's restriction on confidential design files.

## Root Cause
The canvas download endpoint serves the document without checking `viewer_export_restricted`; the same flag is enforced elsewhere (official copy endpoint 403, boot `can_export:false`) for the same user/file — a real backend control this endpoint simply skips.

## Suggested Fix
Apply the same `can_export` / `viewer_export_restricted` check on the canvas download path used by the official export/save-copy paths (403 when set, for view-only and anonymous link visitors).
