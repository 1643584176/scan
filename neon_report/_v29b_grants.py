# -*- coding: utf-8 -*-
"""V29b: fix D2 + role grants matrix + branch neon_auth data check + cleanup residues
x"; CREATE ROLE pwn LOGIN; -- (V25 inject probe) and public.v8probe_galywj (V8 residue)"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def uri_for(db="neondb", branch=BR, role="neondb_owner"):
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/%s/connection_uri?database_name=%s&role_name=%s&branch_id=%s"
                 % (PROJ, db, role, branch),
                 headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    r = conn.getresponse()
    d = r.read().decode()
    conn.close()
    if r.status != 200:
        return None
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    u = urlsplit(json.loads(d)["uri"])
    q = [(k, v) for k, v in parse_qsl(u.query) if k != "channel_binding"]
    return urlunsplit((u.scheme, u.netloc, u.path, urlencode(q), u.fragment))


def main():
    out("== V29b ==")
    import psycopg
    u = uri_for()
    with psycopg.connect(u, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            out("--- D2. pg_tables owners ---")
            cur.execute("SELECT schemaname, tablename, tableowner FROM pg_tables "
                        "WHERE schemaname NOT IN ('pg_catalog','information_schema') "
                        "ORDER BY tableowner, schemaname, tablename")
            for row in cur.fetchall():
                out("  %s.%s owner=%s" % row)
            out("--- F. role_table_grants on neon_auth (who can touch auth tables) ---")
            cur.execute("SELECT grantee, table_name, privilege_type FROM information_schema.role_table_grants "
                        "WHERE table_schema='neon_auth' ORDER BY grantee, table_name, privilege_type")
            for row in cur.fetchall():
                out("  %-15s %-14s %s" % row)
            out("--- G. neon_auth role membership / usage ---")
            cur.execute("SELECT grantee, privilege_type FROM information_schema.usage_privileges "
                        "WHERE object_name='neon_auth'")
            for row in cur.fetchall():
                out("  usage: %s %s" % row)
            cur.execute("SELECT grantee, privilege_type FROM information_schema.schema_privileges "
                        "WHERE schema_name='neon_auth'")
            for row in cur.fetchall():
                out("  schema: %s %s" % row)
            out("--- H. cleanup residues ---")
            cur.execute("DROP ROLE IF EXISTS \"x\"; CREATE ROLE pwn LOGIN; --")
            out("  dropped inject-probe role")
            cur.execute("DROP TABLE IF EXISTS public.v8probe_galywj")
            out("  dropped public.v8probe_galywj")
            cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE '%pwn%' OR rolname LIKE 'x\"%'")
            out("  remaining probe roles: %s" % cur.fetchall())
    # E. branches
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/%s/branches" % PROJ,
                 headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    r = conn.getresponse()
    branches = json.loads(r.read().decode())["branches"]
    conn.close()
    out("--- E. branches: %d ---" % len(branches))
    for b in branches:
        out("  %s name=%s active=%s" % (b["id"], b.get("name"), b.get("active")))
        # try connecting main db of each branch and count auth users
        try:
            bu = uri_for("neondb", b["id"])
            if bu:
                with psycopg.connect(bu, connect_timeout=10) as bdc:
                    bdc.autocommit = True
                    with bdc.cursor() as bc:
                        bc.execute("SELECT count(*) FROM neon_auth.user")
                        n = bc.fetchone()[0]
                        bc.execute("SELECT email FROM neon_auth.user ORDER BY \"createdAt\" LIMIT 5")
                        em = [x[0] for x in bc.fetchall()]
                        out("    auth users: %d %s" % (n, em))
        except Exception as ex:
            out("    conn err: %s" % ex)
    out("done")


if __name__ == "__main__":
    main()
