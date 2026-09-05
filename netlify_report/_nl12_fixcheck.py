# -*- coding: utf-8 -*-
"""NL12: post-submission fix-status check on the database-query surface (read-only + capability probe)
Compare against 9/3 baseline (wave 1-8 + prosecdef audit + allowed_extensions)."""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import COOKIE_B

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'


def q(sql):
    body = {"siteId": SITE_B_ID, "action": "query", "sql": sql}
    conn = http.client.HTTPSConnection("app.netlify.com", timeout=40, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Content-Type': 'application/json',
         'Origin': 'https://app.netlify.com', 'Cookie': COOKIE_B}
    conn.request("POST", "/.netlify/functions/database-query", json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def run(tag, sql):
    st, b = q(sql)
    print("== %s ==" % tag, flush=True)
    print("-> %d %s" % (st, b[:1500]), flush=True)
    return st, b


def main():
    print("== NL12 fix-status check ==", flush=True)
    # 1. version + roles + extension baseline
    run("whoami", "SELECT current_user, version(), current_setting('server_version_num')")
    run("roles", "SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls "
                 "FROM pg_roles WHERE rolname IN ('netlifydb_owner','neon_superuser','cloud_admin') ORDER BY 1")
    run("exts", "SELECT extname, extowner::regrole, extversion FROM pg_extension ORDER BY 1")
    # 2. repack state (if extension present or schema exists)
    run("repack_schema", "SELECT nspname, nspacl FROM pg_namespace WHERE nspname='repack'")
    # 3. prosecdef audit (9/3 baseline: only dblink_connect_u, ACL locked)
    run("prosecdef", "SELECT p.proname, p.proowner::regrole, p.prosecdef, "
                     "aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) AS acl "
                     "FROM pg_proc p WHERE p.prosecdef AND p.pronamespace::regnamespace::text NOT IN "
                     "('pg_catalog','information_schema','pg_toast') ORDER BY 1")
    # 4. can we still CREATE EXTENSION pg_repack? (capability probe; drop immediately if created)
    st, b = run("create_pg_repack", "CREATE EXTENSION IF NOT EXISTS pg_repack")
    if st == 200:
        run("repack_schema_after", "SELECT nspname, nspacl FROM pg_namespace WHERE nspname='repack'")
        run("repack_fn", "SELECT p.proname, p.proowner::regrole, p.prosecdef, p.proacl "
                         "FROM pg_proc p WHERE p.pronamespace::regnamespace::text='repack' ORDER BY 1")
        run("repack_tables", "SELECT tablename, tableowner FROM pg_tables WHERE schemaname='repack' ORDER BY 1")
        run("drop_pg_repack", "DROP EXTENSION pg_repack")
    # 5. allowed_extensions white list (9/3 readable, low-value leak)
    run("allowed_ext", "SELECT unnest(neon.allowed_extensions())")
    # 6. authid readability (by-design, 9/3)
    run("authid", "SELECT count(*) FROM pg_authid")
    print("done", flush=True)


if __name__ == "__main__":
    main()
