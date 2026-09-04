# Netlify Database: tenant "owner" role can read pg_authid — platform role (neon_service) password verifiers exposed

**Product**: Netlify Database (Neon-based PostgreSQL), via the site-level `database-query` function and via direct endpoint connection.

**Summary**: The tenant role `netlifydb_owner` (the highest-privilege role exposed to every Netlify Database customer) is granted membership in `pg_read_all_data` (through `neon_superuser`). PostgreSQL implements `pg_read_all_data` as an ACL-level special case that does *not* exclude `pg_authid` — so the tenant can read `pg_authid` / `pg_shadow` and obtain the SCRAM-SHA-256 password verifiers of all roles on the cluster, **including the platform's internal `neon_service` role** (created by Netlify/Neon provisioning). Verified on two independent tenants/instances. The read-only role (`netlifydb_readonly`, no `pg_*` memberships) is correctly denied — so this is specific to the owner role design, not an accidental public grant.

## Steps to reproduce

Every statement below was executed against my own site's database (two separate sites/teams, both reproduced).

1. Connect as the tenant owner role (either through the app's SQL endpoint as `netlifydb_owner`, or directly via the endpoint with the owner credentials).
2. Read the protected catalog:

```sql
SELECT rolname, rolsuper, rolcanlogin, rolpassword FROM pg_authid;
```

Result (truncated): 21 roles, including:

```
cloud_admin      | superuser | login  | (no password)
neon_service     |           | login  | SCRAM-SHA-256$4096:mvjE...:r0wO...:An2D...   <-- platform role verifier
netlifydb_owner  |           | login  | SCRAM-SHA-256$4096:...
netlifydb_readonly|          | login  | SCRAM-SHA-256$4096:...
```

`pg_shadow` is readable the same way (4 login roles).

3. Root-cause isolation — the access comes from the `pg_read_all_data` membership:

```sql
SET ROLE pg_read_all_data;  SELECT count(*) FROM pg_authid;  -- -> 21 (readable)
SET ROLE pg_write_all_data; SELECT count(*) FROM pg_authid;  -- -> permission denied
SET ROLE pg_monitor;        SELECT count(*) FROM pg_authid;  -- -> permission denied
```

4. Control — the read-only tenant role cannot read it:

```sql
-- as netlifydb_readonly:
SELECT count(*) FROM pg_authid;  -- -> permission denied for table pg_authid
```

5. The catalog ACL itself shows no public/user grant (`{cloud_admin=arwdDxtm/cloud_admin}` only), i.e. the exposure is a direct consequence of the owner role's `pg_read_all_data` membership — PostgreSQL's predefined-role semantics, which Netlify's role model enables for customers.

## Impact

- **Disclosure of platform infrastructure credential material**: the SCRAM-SHA-256 verifier of `neon_service` (a Netlify/Neon internal service role, `rolcanlogin=true`, member of `neon_superuser`) is readable by every database customer, on every instance (verified on two unrelated tenants). PostgreSQL documents `pg_authid` as a catalog that "must not be publicly readable"; access is intended to be superuser-only.
- The verifier enables offline password attacks against the platform role (SCRAM-SHA-256 with 4096 iterations — practical to test against likely passwords; platform service accounts are a high-value target if any reuse/weakness exists).
- The exposure is persistent and systemic: any SQL injection or stolen-credential incident on any Netlify Database tenant immediately yields the same platform verifier, and any future role/password added by provisioning (e.g., if `cloud_admin` is ever assigned a password) would also be exposed.
- Write access is denied (`UPDATE pg_authid` -> permission denied), so impact is read-only disclosure.

## Suggested fix

- Stop granting `pg_read_all_data` (and the other broad `pg_*` memberships) to customer-owned roles in the provisioning model, or
- Deploy the standard hardening used elsewhere for this exact issue: revoke/restrict catalog access so `pg_authid` is readable only by the actual superuser (e.g., custom ACL on `pg_authid`, or a patched role model that excludes catalog access), and
- Consider rotating the `neon_service` credential as a precaution.

## Vendor documentation: this is the documented default design

Follow-up research into public documentation shows this behavior is **by design and fully documented** — likely to be triaged as informative/N-A:

1. **Neon "Manage roles" docs** (`https://neon.com/docs/manage/roles`) explicitly list `pg_read_all_data` (and `pg_write_all_data`, `CREATEDB`, `CREATEROLE`, `BYPASSRLS`, `REPLICATION`, etc.) as part of the `neon_superuser` memberships granted to every project owner role, and describe such roles as "administrator roles". The `netlifydb_owner` role on Netlify Database instances matches this standard Neon role model exactly (verified membership graph).
2. **PostgreSQL predefined-roles docs** describe `pg_read_all_data` as "reading all data (tables, views, sequences), as if having SELECT rights on those objects" — with no exclusion for system catalogs such as `pg_authid`. The ability to read `pg_authid` is a direct consequence of PostgreSQL's predefined-role semantics, not a Netlify/Neon misconfiguration (the catalog ACL shows no explicit grant; the access comes from the kernel-level special case for `pg_read_all_data`).
3. **Neon security docs** make no promise that system catalogs / password verifiers are hidden from tenant owner roles; they do enforce 60-bit-entropy passwords for all roles, which is Neon's compensating control against offline verifier attacks.

Net effect: no documented promise is violated, the role model is vendor-standard, and no working exploit beyond verifier disclosure exists — so this observation is recorded here for reference and Known-findings purposes rather than as a submittable finding.

## Notes

- All testing was read-only and performed on my own sites' databases; no data was modified.
- This issue is independent of the previously reported `pg_repack` privilege-escalation chain (different root cause: role memberships vs. SECURITY DEFINER functions).
