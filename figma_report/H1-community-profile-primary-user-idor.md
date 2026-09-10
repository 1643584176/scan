# Community Profile Primary User IDOR

> **STATUS: N/A (2026-09-07 终判, 存档不提交)**
> 干净状态实测无法复现:primary_user 有 owner 校验(400 Profile does not belong to current user)+ 目标关联校验(400 user not connected);merge 202 无效果(A 不被关联、可正常创建独立 profile)。
> 草稿核心主张仅存在于历史 merge 关联残留窗口期(关联成员共享编辑/切换 primary 是设计内功能),不构成可提交漏洞。
> 证据:v43 PUT 403 / v44 primary_user 双重 400 / v45 merge 202 无效果 / v46 现场恢复。

## Asset
- https://www.figma.com (web app, community profile service)

## Severity
- Medium (CVSS ~5.3: no auth bypass/data read, but public identity impersonation + victim community identity lock, fully silent)

## Weakness
- CWE-284 (Improper Access Control) / CWE-639 (Authorization Bypass Through User-Controlled Key)

## Summary
Any authenticated user can set **any other user** as the `primary_user` of their own community profile via `POST /api/profile/{profile_id}/primary_user` with zero ownership checks. The public profile page (`figma.com/@handle`) then displays the victim's display name/avatar instead of the attacker's — public identity impersonation on figma.com.

Additionally, `POST /api/profile/merge` lets an attacker associate any victim user into their profile without consent, email match, or notification (verified: no email sent). While merged, the victim cannot create their own independent community profile: their `POST /api/profile` request is routed to the attacker's profile (observed: victim's "create" call rewrote attacker profile handle/primary).

Only prerequisite: victim UID, obtainable from any collaboration context (file permissions, comments, team members — user IDs are visible there).

## Steps To Reproduce
Attacker B (UID 1667396392129259941, profile id 1667396392225089633, public handle `pccp_b2_9fmvxl`, display name "boboa"). Victim A (UID 1666382703778278399, display name "pccp").

1. Baseline: `GET https://www.figma.com/@pccp_b2_9fmvxl` → page profile name is **"boboa"**.
2. Switch primary to victim (any UID, no pre-association needed — negative control confirmed):
   ```
   POST /api/profile/1667396392225089633/primary_user
   Cookie: <B session>; X-Figma-User-ID: 1667396392129259941
   {"new_primary_user_id":"1666382703778278399"}
   ```
   → `200 {"meta":{"primary_user_id":"1666382703778278399","name":"pccp",...}}`
3. `GET https://www.figma.com/@pccp_b2_9fmvxl` → profile name now **"pccp"** (victim's name). Attacker's public page impersonates the victim.
4. (Impact extension) Attacker associates victim permanently:
   ```
   POST /api/profile/merge {"primary_user_id":"1667396392129259941","secondary_user_id":"1666382703778278399"}
   ```
   → `200` (no consent/email/notification). Afterwards victim's own `POST /api/profile` (create) returns the attacker's profile id — victim is locked to the attacker's profile and cannot create an independent community identity.
5. Cleanup performed: primary switched back to B, association removed — page restored to "boboa". No persistent state left.

## Impact
- Public identity impersonation: attacker's figma.com community page displays victim's name/avatar; usable for phishing/social engineering under figma.com trust.
- Victim's community identity is captured: victim cannot create/manage an independent profile while associated; silent (no notification).
- Any authenticated user, any victim UID, repeatable.

## Root Cause
`primary_user` and `merge` endpoints never verify that the caller is the target user or an already-authorized member of the profile. Caller and `new_primary_user_id`/`secondary_user_id` are treated as independent inputs.

## Suggested Fix
- `primary_user`: only allow switching primary to the caller's own UID, or to a user that has explicitly confirmed association (e.g. email verification), and require caller to be current primary/associated member.
- `merge`: require target user consent (email/verification code); never silently associate unrelated accounts.
- `POST /api/profile` upsert routing: validate the profile belongs to the requesting user before applying updates.
