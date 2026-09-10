# Reply #2 (short) for H1 #4000158

Hi @h1_analyst_will — correction first: a "viewer-scoped" API key does not exist — `scope` on `POST /api_keys` is silently ignored (bogus values → 200, nothing stored; `_u18_out.txt`). Our key was a full-access personal key; we withdraw the "scoped keys not enforced" note.

Corrected floor: **Editor-or-above**. Re-verified with an admin-minted project-scoped key (Editor by design): fork of restricted branch → 201, `restricted_actions: null` → `connection_uri` → raw rows read (`_u18b_out.txt`).

Core stands regardless of role: Neon 422s `restore` and 57P03s the data plane, yet all six paths reach those same end-states via equivalent operations; forks silently drop `restricted_actions`, and path 6 makes the shared branch serve raw PII while reporting "completed successfully".

Please re-validate on this basis, or state explicitly if Editor+ is considered trusted and the 422/57P03 guardrails out of scope.
