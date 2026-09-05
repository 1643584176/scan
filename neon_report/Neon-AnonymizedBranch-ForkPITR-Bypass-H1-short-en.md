title: Anonymized branch restricted_actions bypass — raw pre-anonymization data recoverable via fork / snapshot / rule-clear (6 paths)

Asset: https://console-stage.neon.build
Severity: HIGH
Weakness: CWE-284 Improper Access Control

## Summary:
Anonymized Branches (static masking) carry `restricted_actions` (restore / delete-rw-endpoint / connect-to-endpoints); docs: "Currently cannot reset to parent, restore, or delete the read-write endpoint for anonymized branches." `restore`/`reset_to_parent` ARE enforced (422) and the data plane is gated (57P03) — but branch **fork** (the vendor's documented main workflow: "the anon branch behaves just like any other Neon branch... branch off of it instantly", "permanently replace PII"), **snapshot create/restore** and **`PATCH masking_rules` + re-anonymize** are not in the enforcement list. All succeed on restricted branches and expose the full original rows:

| # | Path | Result |
|---|------|--------|
| 1 | PITR fork of a fully anonymized branch to its leaked `parent_lsn` | raw data (verified 10s and 180s after completion) |
| 2 | Runtime-failed job (`anon.no_such_fn()`) → `state=error`, data raw | plain fork of current state → raw |
| 3 | `start_anonymization:false` → `initialized`, data raw | plain fork → raw |
| 4 | Column validation runs AFTER creation → HTTP 400 but branch persists (orphan, repeatable) | plain fork → raw |
| 5 | Snapshot create + restore on a failed/initialized/ghost branch | restored child, raw rows (snapshot outlives branch) |
| 6 | `PATCH masking_rules` `[]` + `POST /anonymize` → `state=anonymized` | SAME branch data plane unlocked in place, raw rows |

Control: on a fully masked branch nothing is recoverable (rows overwritten; restore/reset stay 422) — exposure = pre-completion states (initialized/error/ghost) + PITR, all stable, no race.

## Steps To Reproduce:
Own project `orange-sun-90493739` (console-stage.neon.build), header `X-Bug-Bounty: xxbo` on every request.

Setup: `create table u_pii(id int, email text, secret text); insert into u_pii values (1,'alice.real@victimcorp.com','ssn-111-22-3333');`

**1) Create anonymized branch** → 201; response carries `restricted_actions` and leaks `parent_lsn` (= pre-masking fork point):
```http
POST /projects/{pid}/branch_anonymized
{"branch_create":{"branch":{"name":"anon-br","parent_id":"<src>"},"endpoints":[{"type":"read_write"}]},
 "masking_rules":[{"database_name":"neondb","schema_name":"public","table_name":"u_pii","column_name":"email","masking_function":"anon.fake_email()"}],
 "start_anonymization":true}
```
Control: `POST /branches/{anon-br}/reset_to_parent` → **422** "cannot restore anonymized branches".

**2) Path 1 — PITR fork (any time after completion):**
```http
POST /projects/{pid}/branches
{"branch":{"name":"f","parent_id":"<anon-br>","parent_lsn":"0/3417598"},"endpoints":[{"type":"read_write"}]}
→ 201, restricted_actions: null
```
`select * from u_pii;` → `alice.real@victimcorp.com / ssn-111-22-3333` (full original rows).

**3) Paths 2–4 — no fork params:** same create with `"masking_function":"anon.no_such_fn()"` → 201, ~10s later `state=error` (raw data, 57P03, lock kept); or `start_anonymization:false` (initialized); or a non-existent `column_name` → HTTP 400 but the branch persists (ghost). Plain fork (no params) of any of these → 201, `restricted_actions: null`, raw rows readable.

**4) Paths 5/6 — no fork:** on the failed/initialized branch: `POST /branches/{id}/snapshot` → 200, `POST /snapshots/{sid}/restore` → 200 → new branch with raw rows; and `PATCH /branches/{id}/masking_rules` `{"masking_rules": []}` → 200 (ungated) → `POST /branches/{id}/anonymize` → 200 → `state=anonymized` ("no masking rules defined") → `connect-to-endpoints` auto-released → same branch serves raw rows directly.

## Impact:
- "cannot restore anonymized branches" / "permanently replace PII" bypassed through the vendor's documented main workflow (fork) and ungated snapshot/state-machine channels — CWE-284, systemic multi-endpoint gap (single-endpoint fix remains bypassable).
- Full original data (masked and unmasked columns) recoverable for the branch's whole lifetime; stable states (no race); path 4 endlessly repeatable; path 6 zero artifacts (stealthiest).
- Vendor-published use case "Contractor or partner access... without giving access to actual user data" → low-trust member with fork rights recovers raw PII; compliance controls (data minimization/GDPR) void.
- HIGH: the feature's documented purpose is sharing data copies with low-trust parties — vendor blog use case "Contractor or partner access... without giving access to actual user data", and the new per-project permission model hides even connection strings from Viewer — so a fork-capable member recovers raw PII the vendor promised would stay masked; the data owner's data is exposed to a party that has no production access rights (data-isolation failure inside the project boundary; not cross-tenant, see Not claimed).
- Not claimed: cross-tenant access, production-tenant compromise.

## Root cause:
1. `restricted_actions` enforcement list misses fork (incl. PITR params), snapshot create/restore, `PATCH masking_rules`, `POST /anonymize`, `set_as_default`.
2. Forked/restored children do not inherit `restricted_actions` (null).
3. `branch_anonymized` non-atomic: validation after creation → HTTP 400 leaves an orphan initialized branch.
4. Data-plane lock released on job state (`anonymized`), not on masking evidence → empty-rule job unlocks raw data in place.

## Suggested fix:
1. Gate fork on restricted parents: reject PITR params earlier than completion LSN; reject error/initialized/anonymizing states; children inherit `restricted_actions`.
2. Apply the same checks to snapshot create/restore.
3. Terminal state for failed jobs (auto-delete / safe retry); atomic branch creation with rollback.
4. Gate `PATCH masking_rules` + `POST /anonymize` while restricted; release data plane on masking evidence only (non-empty rules, rows affected > 0).
5. Audit all timeline/state-changing endpoints (restore, reset, fork, import, snapshot, masking-rules, anonymize, set_as_default).

## Impact:
HIGH (security-function bypass + raw PII recovery in the vendor-documented low-trust sharing scenario; systemic 6-path gap; role floor unverifiable on single-user staging — viewer-scoped keys not enforced on the staging API — disclosed to triage). All tests on own project, self-generated dummy data, branches deleted immediately, project `main` untouched, zero destructive operations, `X-Bug-Bounty: xxbo` on all requests.

## Attachments:
Detailed evidence (test scripts + raw outputs for all six paths) available on request.
