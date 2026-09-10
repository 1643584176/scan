# Weave paywall bypass: free account makes private workflow publicly readable via API (server-side tier check missing on share/visibility)

**STATUS: 等待提交**(H1 提交配额已用尽,待配额恢复后提交;证据完整,见文末 Evidence)

## Asset
Figma Weave (app.weavy.ai / api.weavy.ai)

## API
- `PUT https://api.weavy.ai/api/v1/recipes/{id}` body `{"visibility":"public"}`
- `POST https://api.weavy.ai/api/v1/recipes/{id}/share` body `{"emails":["x@example.com"]}`
- `PUT https://api.weavy.ai/api/v1/tools/{id}/visibility` / `POST https://api.weavy.ai/api/v1/tools/{id}/share` (same flaw, second asset type)
- `GET https://api.weavy.ai/api/v1/recipes/{id}` and `GET https://api.weavy.ai/api/v1/tools/{id}/view` (anonymous read channels)
- Control: `POST https://api.weavy.ai/api/v1/workspaces/{ws}/members/invite`

## Severity
Medium (Low-Medium) — CWE-284 Improper Access Control / missing paywall enforcement with confidentiality impact

## Summary
Sharing in app.weavy.ai is a paid feature: free accounts see "Sharing is only available on paid plans" and the share UI is locked. This gate is client-side only. The server performs **no tier check** on recipe share/visibility endpoints, while sibling paywalled endpoints (workspace member invite) do return `400 "Cant invite members to non team subscription"`. A free account can flip a private workflow to `visibility=public` via a direct API call, after which **any anonymous user can read the full workflow content**; the same applies to email-sharing. Owners relying on the UI (which shows sharing as unavailable) have no indication their private workflow became publicly readable.

## Steps
1. Free account (Google SSO, `subscription_type: free`). Share modal locked: "Sharing is only available on paid plans".
2. Create workflow `CLOID63hXfPGwO72C6tYzt` (default `visibility: private`).
3. Baseline — anonymous: `GET /api/v1/recipes/CLOID63hXfPGwO72C6tYzt` → `403 {"internalErrorCode":1030,"message":"Unauthorized to access recipe"}`.
4. Free account: `PUT /api/v1/recipes/CLOID63hXfPGwO72C6tYzt` `{"visibility":"public"}` → `200`.
5. Anonymous (no auth, no cookie): `GET /api/v1/recipes/CLOID63hXfPGwO72C6tYzt` → `200` returning the full workflow JSON (24.8 KB): 8 nodes including a `promptV3` "Video Prompt" node and a `custommodelV2` node with model config (`luma/ray-3-2`), plus 3 edges — real private design content.
6. Revert: `PUT ... {"visibility":"private"}` → `200`; anonymous GET → `403` again (revocation works; the gap is the missing tier gate, not revocation).
7. Free account: `POST /api/v1/recipes/CLOID63hXfPGwO72C6tYzt/share` `{"emails":["nobody-test@example.com"]}` → `201`; share entry persisted in `sharedUsers`.
8. Control — workspace member invite (also a paid feature, same free account): `POST /api/v1/workspaces/180f334e-710b-4c81-884d-7ebf26e7b6eb/members/invite` `{"emails":["ctl-1@example.com"],"userRole":"Member"}` → `400 {"internalErrorCode":1008,"message":"Cant invite members to non team subscription"}` → server-side tier enforcement exists elsewhere and is missing on recipe share/visibility.
9. Second asset type (published tool/design-app, same ID): anonymous `GET /api/v1/tools/CLOID63hXfPGwO72C6tYzt/view` → `403`; free account `PUT /api/v1/tools/CLOID63hXfPGwO72C6tYzt/visibility` `{"visibility":"public"}` → `204`; anonymous view → `200`; free account `POST /api/v1/tools/CLOID63hXfPGwO72C6tYzt/share` `{"emails":["ctl-tool@example.com"]}` → `201`.
10. All visibility scopes are settable, not just public: `PUT /recipes/{id}` `{"visibility":"team"}` → `200`, `{"visibility":"organization"}` → `200` (no tier/scope check on any of them).

## Impact
Free-tier users can bypass the paywall and expose private workflow content (node graph incl. prompts and model configuration) to anonymous read access — verified on both asset types: after the API flip, an unauthenticated request received the complete 8-node workflow JSON (recipe) and the tool became anonymously viewable (tool). The UI's privacy posture ("sharing only on paid plans") is misleading: content the owner believes private can become publicly readable, and the UI offers no path to ever reproduce this state.

Evidence: `_w55_anon_full_content.json` (full anonymous response), `_w55_closure_log.txt`, `_w54_evidence_chain.txt` (in report workspace).

## Root Cause
Tier/subscription check missing server-side on recipe and tool share/visibility (and recipe publish) endpoints; workspace-member endpoints implement the check (error 1008).

## Fix
Apply the same subscription enforcement used by `/workspaces/{id}/members/invite` to recipe/tool share/visibility/publish endpoints.
