# Figma H1 Submission (community profile forced merge) — 2026-09-07

> STATUS: 已提交 (2026-09-07), 等待 H1 回复

Title: No consent check in profile merge endpoint allows silent community identity takeover and impersonation

Severity: MEDIUM
Weakness: CWE-284 Improper Access Control / CWE-639 Authorization Bypass Through User-Controlled Key
Asset: https://www.figma.com (web app, community profile service)

## Summary
`POST /api/profile/merge` lets **any user** force-associate **any other user** (who has a community profile) into their own profile, with zero consent from the target and no notification. After the silent merge:
1. The victim's independent community profile disappears from the public site (`figma.com/@victim` → 404) and becomes unreachable via API.
2. The victim is locked: their own `POST /api/profile` calls are routed into the attacker's profile (`400 "Primary user does not reference profile"` or the attacker's profile id is returned and the attacker's handle is overwritten by the victim's requests).
3. The attacker switches the profile primary to the victim (`POST /api/profile/{attacker_pid}/primary_user` → 200) and their public page `figma.com/@attacker` now displays the victim's name/avatar — public identity impersonation on figma.com.
4. The attacker (or any associated user) can also remove the original owner from the profile (`DELETE /api/profile/{pid}/user` → 200), taking full control.

Only prerequisite: victim UID, obtainable from any collaboration context (file viewers, comments, team members — user IDs are visible there).

## Steps To Reproduce
Attacker B (UID 1667396392129259941, profile `pccp_b2_9fmvxl`, display "boboa"). Victim A (UID 1666382703778278399).

1. Victim baseline: A creates an independent community profile → `GET https://www.figma.com/@pccp_a_v50` returns 200 (profile exists).
2. Attacker force-merges the victim (no consent, no notification):
   ```
   POST /api/profile/merge
   Cookie: <B session>; X-Figma-User-ID: 1667396392129259941
   {"primary_user_id":"1667396392129259941","secondary_user_id":"1666382703778278399"}
   ```
   → `200 {"meta":{"id":"1667396392225089633",...}}`; afterwards `GET /api/profile` (as B) shows A in `associated_users` with `is_primary_user: false`.
3. Victim's independent profile is gone: `GET https://www.figma.com/@pccp_a_v50` → **404**. Victim's own profile read `POST /api/profile {"primary_user_id":<A>}` → **400 "Primary user does not reference profile"**.
4. Attacker takes over the public identity:
   ```
   POST /api/profile/1667396392225089633/primary_user
   {"new_primary_user_id":"1666382703778278399"}
   ```
   → `200`; `GET https://www.figma.com/@pccp_b2_9fmvxl` now shows profile name **"pccp"** (the victim's) instead of "boboa".
5. Victim is locked: while merged, the victim's own create attempt `POST /api/profile {"primary_user_id":<A>,"profile_handle":"x"}` returns the **attacker's profile id** (1667396392225089633) and rewrites the attacker profile's handle.
6. Cleanup performed by tester: primary switched back to B, A removed from the profile, victim profile restored and deleted. No persistent state left.

## Impact
- **Silent identity takeover**: any authenticated user can absorb any other user's community identity without consent — victim's public profile vanishes and cannot be recreated while the association lasts.
- **Public impersonation**: attacker's figma.com page displays the victim's name; usable for phishing/social engineering under figma.com trust.
- **Victim lock-out**: victim cannot create/manage an independent community profile while associated; no notification is sent.
- Repeatable with any victim UID; the only requirement is that the victim has created a community profile at least once.

## Root Cause
`POST /api/profile/merge` never verifies that the target user (`secondary_user_id`) consented to (or is otherwise entitled to) being merged into the caller's profile. The merge endpoint establishes the profile association (`associated_users`) that downstream endpoints (`primary_user`, `user` delete) trust without re-validating consent, so the attacker can then impersonate the victim and even remove the original owner.

## Suggested Fix
- `merge`: require explicit consent of `secondary_user_id` (email verification or in-product confirmation) before associating the account; never silently merge unrelated accounts.
- Enforce role separation in the shared profile: a secondary member who was added without consent should not be able to switch `primary_user` or delete the original primary.
- `POST /api/profile` upsert routing: only the primary/owner user's requests should upsert the profile; associated users' create requests should not be routed into it.
