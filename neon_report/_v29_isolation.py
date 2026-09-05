# -*- coding: utf-8 -*-
"""V29: isolation boundary scan - can we see OTHER tenants' data?
A. pg_database list (other DBs on same instance?)
B. pg_roles (instance-level roles - other tenants' roles visible?)
C. all schemas + tables (non-neon_auth objects?)
D. pg_stat_activity (other connections/queries?)
E. branch list via console API + check each branch DB for neon_auth rows"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"
NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"


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
    out("== V29 isolation boundary scan ==")
    import psycopg
    u = uri_for()
    with psycopg.connect(u, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            out("--- A. pg_database ---")
            cur.execute("SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database ORDER BY datname")
            for row in cur.fetchall():
                out("  db: %s (%s)" % row)
            out("--- B. pg_roles (instance-level, non-default) ---")
            cur.execute("SELECT rolname, rolsuper, rolcreaterole, rolcanlogin FROM pg_roles "
                        "WHERE rolname NOT LIKE 'pg_%' ORDER BY rolname")
            for row in cur.fetchall():
                out("  role: %s super=%s createrole=%s login=%s" % row)
            out("--- C. schemas + tables ---")
            cur.execute("SELECT table_schema, table_name FROM information_schema.tables "
                        "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
                        "ORDER BY table_schema, table_name")
            for row in cur.fetchall():
                out("  %s.%s" % row)
            out("--- D. pg_stat_activity ---")
            cur.execute("SELECT datname, usename, state, left(query,60) FROM pg_stat_activity "
                        "WHERE state IS NOT NULL")
            for row in cur.fetchall():
                out("  %s" % (row,))
            out("--- D2. tables owned by others? ---")
            cur.execute("SELECT table_schema, table_name, tableowner FROM pg_tables "
                        "WHERE schemaname NOT IN ('pg_catalog','information_schema') "
                        "ORDER BY tableowner, schemaname, tablename")
            for row in cur.fetchall():
                out("  %s.%s owner=%s" % row)
    # E. branch list
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/%s/branches" % PROJ,
                 headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    r = conn.getresponse()
    branches = json.loads(r.read().decode())["branches"]
    conn.close()
    out("--- E. branches: %d ---" % len(branches))
    for b in branches:
        out("  branch: %s name=%s active=%s" % (b["id"], b.get("name"), b.get("active")))
    out("done")


if __name__ == "__main__":
    main()
