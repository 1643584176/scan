# Reply #2 for H1 #4000158 (2026-09-11) — answer to "How exactly can you generate a viewer-scoped API key via UI?"

Hi @h1_analyst_will — direct answer: **you cannot, and we have to correct our own wording here.**

**1) There is no viewer-scoped API key — not via UI, not via API.**
The Console offers exactly three key types: Personal (inherits the member's own access), Organization, and Project-scoped — and per the docs, project-scoped keys carry **Editor** access on their project ("Create new → Project-scoped" in Org Settings → API keys). There is no viewer option anywhere.
Our earlier claim came from a wrong assumption on our side: we created a key via `POST /api_keys` and added a non-schema `scope` object `{"project_id":..., "permission":"viewer"}`. We re-tested this on staging (`_u18_out.txt`):

- `scope` with `"permission":"totally-bogus"` → **200**
- `scope` as a string instead of an object → **200**
- an arbitrary unknown field → **200**
- nothing scope-like is echoed in the create response or readable in `GET /api_keys`

i.e., the field is silently ignored (unknown JSON is dropped; there is no validation), so that key was a **plain full-access personal API key**. We withdraw the report note "`permission: viewer` scoped keys are NOT enforced on the staging API layer" — that was wrong; those 200s came from a normal personal key. Apologies for the noise.

**2) Corrected answer to "what permission level is needed": Editor-or-above on the project** — an Editor/Admin member's credential, or the admin-minted **project-scoped key**, which is the *most restricted* key type that exists (Editor on one project by design). We reproduced the full chain under exactly that key type (`_u18b_out.txt`):

- create project-scoped key (`POST /organizations/{org}/api_keys` `{"key_name":"...","project_id":"<pid>"}`) → 200
- fork the restricted raw-state anonymized branch with **only that key** → 201, child `restricted_actions: null`
- `GET connection_uri` for the child with that key → 200
- `SELECT` → **raw rows** (`alice.real@victimcorp.com` / `ssn-111-22-3333`) — RAW=True

So the floor we can demonstrate is Editor-or-above member access; Viewer/Collaborator behavior remains untestable on single-user staging (unchanged disclosure).

**3) Why this is still a security issue, not product polish** (independent of the role answer):

On your earlier point — that a member could read the source data anyway: the delta is not readability, it is that **Neon itself enforces this exact boundary against this exact actor class** (`restore`/`reset_to_parent` → 422, data plane → 57P03 on the anonymized branch), and our six paths reach those forbidden end-states through unlisted equivalent operations — an enforcement bypass by definition. The harm is also two-sided: Neon's own documented fork workflow silently produces raw-data copies with `restricted_actions: null` that nothing distinguishes from properly anonymized branches, and path 6 flips the *shared* branch in place to serve raw PII while reporting "completed successfully (no masking rules defined)". External recipients of the connection string — the documented protection target — then read PII through a control that reports success and leaves no artifact for review. A member hand-reading the source is detectable and attributable; these paths are silent, persistent (snapshots outlive the branch), and mislabel unmasked data as anonymized — a protection-mechanism failure (CWE-693), not a data-handling policy question.

- Neon itself 422s `restore`/`reset_to_parent` and gates the data plane with 57P03 — the vendor's own model says an API actor must not be able to recover pre-masking data from the anonymized branch. Our six paths reach exactly those forbidden outcomes through unlisted operations: PITR fork ≡ reset-to-parent (`parent_lsn` is even returned by the creation response), snapshot create/restore ≡ restore (restore is 422; this channel is 200 and the snapshot outlives the branch), and path 6 auto-releases `connect-to-endpoints` **in place** while the job reports "completed successfully (no masking rules defined)".
- The guard flag is silently stripped: children come back `restricted_actions: null` and are never inherited — so the vendor-documented fork workflow ("the anon branch behaves just like any other Neon branch... you can branch off of it instantly") produces raw-data copies **with no marker that they are unmasked**, and path 6 leaves the *shared* branch itself serving raw rows to connection-string recipients — the exact party the feature is documented to protect.
- "Permanently replace PII" is the guarantee data-minimization/compliance relies on; today it is falsifiable by routine operations that end in an apparently-anonymized state (path 4 is endlessly repeatable; path 6 leaves zero artifacts), and if the source branch is retired the restricted branch fully retains the pre-masking history (PITR/`parent_lsn`).

**4) Ask:** please re-validate on this corrected basis (logs: `_u18_out.txt`, `_u18b_out.txt`, plus per-path outputs `_u8*`–`_u16b*`). If the team's position is that Editor+ credentials are inherently trusted here and the 422/57P03 guardrails are out of scope, we'd ask you to state that explicitly so we can calibrate severity. If a viewer-role member can be enabled on staging, we will gladly close the role question against it.

All tests: own project, dummy data, every branch deleted, key revoked, `X-Bug-Bounty: xxbo` on all requests.
