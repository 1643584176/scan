# Reply draft for H1 #4000158 (triage: h1_analyst_will, 2026-09-10)

Hi @h1_analyst_will, thanks for the review — happy to clarify the permission question.

**1) Minimum credential (direct answer).**
On the provided asset (console-stage.neon.build) the attacker does not need to be a project member at all, and does not need admin/member/collaborator access. A **viewer-scoped API key** — the lowest-privilege credential of the Aug-2026 per-project permission model (`POST /api_keys` with `{"scope":{"project_id":"<pid>","permission":"viewer"}}`) — completed the full chain end-to-end. Everything below was executed with that viewer-scoped key alone (owner key only to mint it):

- fork of the restricted raw-state anon branch (`POST /projects/{pid}/branches`, parent = initialized/error anon branch) → 201, `restricted_actions: null`
- `GET /connection_uri` for the child → 200 (full URI incl. password)
- `SELECT * FROM u17b_pii` → raw rows (`alice.real@victimcorp.com` / `ssn-111`)

Scope sanity probes under the same key: branch rename 200, branch delete 200, `set_as_default` 200, `reset_password` on `main` 200 (returns the new password), `branch_anonymized` passed authz and failed only at masking-rule validation, `GET /connection_uri` (`main`) → 200 with a working password. In other words, on the tested environment the scoped-key model is not enforced at the API layer at all — we disclosed this in the report ("role floor unverifiable on single-user staging"). In an environment where scopes are enforced, the minimum would be an Editor-class role (what can create branches); but the credential model is precisely the vehicle the feature is meant to be shared with (contractors/partners/tools), and here the lowest scope already suffices.

**2) Why "members can read the source anyway" does not apply.**
The vendor's own enforcement defines the security boundary: `reset_to_parent`/`restore` → 422 ("cannot restore anonymized branches") and the data-plane gate → 57P03 exist specifically to stop an **API-authenticated actor** from recovering pre-masking data. A connection-string recipient cannot call these endpoints at all — so these controls only have meaning against project API users, i.e. exactly the actor class that "already has direct access". If that actor were implicitly trusted with the raw data, the 422s and the 57P03 gate would be pointless, and "Currently cannot reset to parent, restore..." / "permanently replace PII" would be false as written.

Our six paths reach the exact outcomes those controls forbid, through sibling endpoints:
- `parent_lsn` PITR fork ≡ reset-to-parent — and the creation response leaks the pre-masking fork point (`parent_lsn`);
- snapshot create/restore ≡ restore (restore itself is 422; the snapshot channel is ungated, and the snapshot outlives the branch);
- path 6 releases `connect-to-endpoints` **in place** on the same branch (state=anonymized, "completed successfully (no masking rules defined)") — the same branch whose connection string is shared with external recipients per the documented use case.

So the external party the feature is designed to protect ends up reading raw PII from an artifact that still presents as masked. `restricted_actions` is dropped to `null` on every fork/restore child and is never inherited; children and snapshots persist after the parent is deleted — the "anonymized" invariant is silently destroyed with no way for a recipient or auditor to detect it.

**3) Request.**
Please re-validate the six paths. They are stable (verified 10s and 180s after completion, no race), and the negative control on a fully masked branch recovers nothing — the exposure is specifically the pre-completion states + PITR. Full raw request/response logs and scripts are available for every path, including the viewer-scope chain (`_u17*` outputs). If the team's position is that this restriction is not a security boundary, we would ask for that to be stated explicitly, since both the documentation and the shipped 422/57P03 behavior assert the opposite.

All testing was performed on our own project with self-generated dummy data; every branch was deleted immediately; `X-Bug-Bounty: xxbo` was sent on every request.
