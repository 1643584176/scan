# 标题 必填
title: Anonymized Branch restricted_actions bypass via branch fork — full recovery of pre-anonymization data (PITR + failed/initialized/ghost states)

# 资产 必填
Asset: https://console-stage.neon.build

# 严重程度 必填
Severity: MEDIUM

# 弱点 必填
Weakness: CWE-284 Improper Access Control

# 描述 必填
## Summary:
Neon's Anonymized Branch feature (static masking beta) marks the created branch with `restricted_actions` — `restore` ("cannot restore anonymized branches"), `delete-rw-endpoint` and `connect-to-endpoints` — to prevent the anonymized branch (and its raw data) from being rolled back / accessed. These restrictions ARE enforced on the control plane (`reset_to_parent`/`restore` → 422) and on the data plane (proxy → 57P03).

However, `POST /projects/{pid}/branches` (branch fork) is **not** in the restricted_actions enforcement list: forking an anonymized branch neither checks the parent's restrictions nor makes the child inherit them (`restricted_actions: null`), and it fully supports `parent_lsn`/`parent_timestamp` PITR parameters. A coverage audit (same session) shows this is not a single-endpoint gap: `restore`/`reset_to_parent` are gated (422), but fork, the snapshot lifecycle and masking-rule mutation are all unlisted. Six reachable paths all produce raw pre-anonymization data:

1. **PITR fork**: fork the anonymized branch back to its timeline start LSN (creation response leaks `parent_lsn`, which predates the masking UPDATE) → raw data, time-independent (verified 10s and 180s after anonymization completed).
2. **Failed-job state (no params)**: submit `branch_anonymized` with a `masking_function` that only fails at runtime (e.g. `anon.no_such_fn()`); the branch lands in `state=error` — data is fully raw (failed single-statement UPDATE = 0 rows changed), data plane permanently disabled (57P03), lock permanently kept. A plain fork of its current state → raw-data child.
3. **Never-started state (no params)**: `start_anonymization: false` → branch stays `initialized` with raw data, then plain fork → raw-data child.
4. **Ghost branch**: column-name validation runs AFTER branch creation → request returns 400 but the branch already exists (initialized, raw data, locks, data plane disabled); the client treats 400 as failure and never cleans up → orphan branch persists, plain fork → raw-data child.
5. **Snapshot lifecycle (no fork needed)**: on a failed / never-started / ghost branch (raw data), `POST /branches/{id}/snapshot` returns 200 and `POST /snapshots/{sid}/restore` returns 200 → new branch with `restricted_actions: null` and the full original rows (restore semantics are explicitly forbidden by restricted_actions — `restore`/`reset_to_parent` are 422 — but the snapshot channel is ungated).
6. **Rule-clear + re-anonymize (data plane unlocked in place, no child branch at all)**: on an `initialized` branch (raw data, data plane 57P03): `PATCH /branches/{id}/masking_rules` with `{"masking_rules": []}` returns 200, then `POST /branches/{id}/anonymize` returns 200 and the job reaches `state=anonymized` ("no masking rules defined") → the `connect-to-endpoints` restriction is auto-released (verified state machine) → the SAME branch's data plane now serves the raw rows directly. The lock release condition (job reached `anonymized`) is decoupled from the actual data-safety condition (rows really masked).

## Steps To Reproduce:
All on own project `orange-sun-90493739` (console-stage.neon.build), `X-Bug-Bounty: xxbo` on every request.

**Setup** (source branch `br-src`):
```sql
create table u_pii(id int, email text, secret text);
insert into u_pii values (1,'alice.real@victimcorp.com','ssn-111-22-3333');
```

**1) Create anonymized branch (data-owner operation):**
```http
POST /api/v2/projects/{pid}/branch_anonymized
{
  "branch_create": {"branch": {"name": "anon-br", "parent_id": "<br-src>"},
                     "endpoints": [{"type": "read_write"}]},
  "masking_rules": [{
    "database_name": "neondb", "schema_name": "public",
    "table_name": "u_pii", "column_name": "email",
    "masking_function": "anon.fake_email()"}],
  "start_anonymization": true
}
→ 201, branch carries restricted_actions: restore / delete-rw-endpoint / connect-to-endpoints
```
After anonymization completes, `anon-br` serves masked data only. Negative control: `POST /branches/{anon-br}/reset_to_parent` → 422 "cannot restore anonymized branches" (enforcement exists for restore).

**2) ★ Bypass — PITR fork (path 1):** the 201 response of the anonymized branch contains `parent_lsn` (e.g. `0/3417598` = fork point from source = before the masking UPDATE). Later:
```http
POST /api/v2/projects/{pid}/branches
{"branch": {"name": "fork-back", "parent_id": "<anon-br>", "parent_lsn": "0/3417598"},
 "endpoints": [{"type": "read_write"}]}
→ 201, restricted_actions: null
```
```sql
select * from u_pii;
-- (1, 'alice.real@victimcorp.com', 'ssn-111-22-3333')   ← full original data
```
Same result via `parent_timestamp`, and immediately (~10s) or 180s after anonymization completes.

**3) ★ Bypass without any fork parameters (paths 2/3/4):**
```http
POST .../branch_anonymized   # masking_function: "anon.no_such_fn()"  (runtime error only)
→ 201; ~10s later state=error ("Anonymization failed: function anon.no_such_fn() does not exist")
```
The branch now holds fully raw data + data plane disabled (57P03) + lock kept (reset → 422). Then:
```http
POST /api/v2/projects/{pid}/branches
{"branch": {"name": "fork-err", "parent_id": "<failed-br>"},
 "endpoints": [{"type": "read_write"}]}
→ 201, restricted_actions: null → reads complete original rows.
```
Same result for `start_anonymization: false` (state `initialized`) and for the ghost-branch variant where a non-existent `column_name` returns HTTP 400 but leaves the branch behind (`u11-failcol`, state ready + locks + raw data) — fork → raw data.

**4) Paths 5/6 — no fork at all (u16 series):**
```http
# path 5: snapshot channel on the failed branch (state=error, raw data)
POST /projects/{pid}/branches/{failed-br}/snapshot?name=s
→ 200  (restricted_actions NOT checked)
POST /projects/{pid}/snapshots/{sid}/restore          # no target → new branch
→ 200, restricted_actions: null
# SQL on the restored branch → alice.real@victimcorp.com ... (full original rows)

# path 6: rule-clear + re-anonymize on an initialized branch (start=false, raw data, 57P03)
PATCH /projects/{pid}/branches/{init-br}/masking_rules
{"masking_rules": []}                                 # → 200 (NOT gated)
POST /projects/{pid}/branches/{init-br}/anonymize      # → 200
# status → state=anonymized "Anonymization completed successfully (no masking rules defined)"
# connect-to-endpoints auto-released → SAME branch data plane serves raw rows directly
```
Control: on a fully anonymized (masked) branch the same operations cannot recover anything (data already overwritten; `restore`/`reset_to_parent` stay 422).

## Impact:
- The product-declared property "cannot restore anonymized branches" is bypassed by semantically equivalent operations (fork+PITR, snapshot create+restore, rule-clear+re-anonymize), CWE-284 (enforcement list and operation list disagree) — a systemic multi-endpoint gap, not a single fork omission.
- Forking an anonymized branch is not an edge endpoint but the vendor's documented **main workflow** (2025-05-15 blog: "the anon branch behaves just like any other Neon branch... You can branch off of it instantly"; docs: anonymized branches "permanently replace PII", rerunning applies rules "to previously anonymized data, not fresh data from the parent branch"). Vendor-published use cases include "**Contractor or partner access.** Share a branch of your database for testing or demos, **without giving access to actual user data**". Verified: forking the current state of initialized/error/ghost anonymized branches (no params) or PITR-forking an anonymized branch returns the full original rows → the feature's core data-safety promise fails in its primary sharing scenario.
- Full original data (masked and unmasked columns, all rows before the masking LSN) recoverable from any anonymized branch for its whole lifetime.
- Paths 2–6 are stable states, not races: failed / never-started / ghost anonymized branches exist indefinitely; path 4 is endlessly repeatable (each 400 request leaks one more orphan branch).
- Path 6 is the most stealthy: zero child-branch artifacts, the original branch's data plane is unlocked in place; combined with ghost branches an attacker can mass-produce orphan `initialized` branches (400 loop) and drain each one without leaving new resources.
- Attack chain is 2 API calls and needs only project API access with fork/mutation permission (EDITOR; the project-scope role floor is unverifiable on single-user staging).
- Compliance scenario: anonymized branches used to share production-derived data with low-trust collaborators (project members) → collaborator restores raw PII, masking rendered useless.

## Root cause:
1. `restricted_actions` enforcement covers reset/restore/endpoint ops (422 — incl. `POST /branches/{id}/restore` with `source_branch_id`) and data-plane connections (57P03) but **not** branch fork (incl. PITR params), snapshot create/restore, `PATCH masking_rules`, `POST /branches/{id}/anonymize`, or `set_as_default`.
2. Restricted actions are only applied at anonymized-branch creation; **forked/restored children do not inherit them** (child `restricted_actions: null`).
3. `branch_anonymized` is not atomic: column validation runs after branch creation (HTTP 400 still leaves a created, initialized, locked branch behind; no rollback).
4. Lock release is state-machine-driven, not data-driven: `connect-to-endpoints` is removed when the job reaches `anonymized`, so an empty-rule job ("no masking rules defined") releases the data plane while rows are still fully raw.

## Suggested fix:
1. When the parent branch carries `restricted_actions`, reject fork `parent_lsn`/`parent_timestamp` earlier than the anonymization-completion LSN (or reject PITR params entirely) and reject forking anonymized branches in error/initialized/anonymizing states.
2. Make forked children inherit the parent's restricted_actions (currently dropped); same for snapshot-restored branches.
3. Terminal handling for failed anonymization jobs (currently "raw data + data plane disabled + lock forever", no retry path) — auto-delete or safe retry; make branch creation atomic/transactional (rollback on validation failure).
4. Gate `PATCH masking_rules` and `POST /branches/{id}/anonymize` on restricted branches, and tie data-plane release to actual masking evidence (non-empty rule set with rows affected > 0) instead of the job state machine alone.
5. Audit every branch-timeline/state-changing endpoint (restore, reset, fork, snapshot create/restore, import, masking-rules PATCH, `POST /branches/{id}/anonymize`, set_as_default) against the restricted_actions list.

# 影响 必填
## Impact:
- Severity: conservative MEDIUM (security-control bypass + sensitive-data recovery with project-level API access). Would be HIGH if Neon positions Anonymized Branches as safe to share with low-trust/external collaborators (fork-permission member recovers raw production PII independently). The derived-surface audit (paths 5/6) shows the gap is systemic (multiple unlisted endpoints), so single-endpoint fixes would remain bypassable.
- All tests on own project with self-generated dummy data (fake emails/SSNs); branches created and deleted immediately, project `main` untouched; zero destructive operations; no real user data involved.

# 附件 非必填
## Attachments:
- Evidence scripts/outputs (available on request): `_u8_forkpitr.py/_u8_out.txt` (path 1: parent_lsn + parent_timestamp), `_u9_forkconfirm.py/_u9_out.txt` (180s time-independence), `_u11_failstate.py/_u11_out.txt` (failed states + 57P03 + fork 201), `_u12_forkfailed.py/_u12_out.txt` (raw data from fork of failed branch), `_u14_anon_state.py/_u14_out.txt` (initialized state machine + enforcement model), `_u15_ghost.py/_u15_out.txt` (400 ghost branch + fork recovery), `_u16_derived.py/_u16_out.txt` (paths 5/6: snapshot channel RAW=True; rule-clear + re-anonymize unlocks data plane in place), `_u16b_restore.py/_u16b_out.txt` (control: restore endpoint 422-gated). All requests carried `X-Bug-Bounty: xxbo` on console-stage.neon.build.
