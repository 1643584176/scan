# -*- coding: utf-8 -*-
"""V31b: C. Data API schema/functions inventory  D. project_config full dump"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def main():
    out("== V31b ==")
    # C. Data API: OpenAPI-ish endpoints /rpc probe + schema table list via root
    # first get JWT
    conn = http.client.HTTPSConnection("ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build",
                                       timeout=30, context=ctx)
    h = {"Content-Type": "application/json", "Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"}
    conn.request("POST", "/neondb/auth/sign-in/email",
                 json.dumps({"email": "libobo1229+na_org1@gmail.com", "password": "SecTest!2026pass"}).encode(),
                 headers=h)
    r = conn.getresponse()
    r.read()
    cks = r.headers.get_all("Set-Cookie")
    conn.close()
    cookie_all = "; ".join(c.split(";")[0] for c in cks)
    conn = http.client.HTTPSConnection("ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build",
                                       timeout=30, context=ctx)
    conn.request("GET", "/neondb/auth/token", headers={"Cookie": cookie_all})
    r = conn.getresponse()
    jwt = json.loads(r.read().decode()).get("token")
    conn.close()
    out("jwt ok")
    DA = "ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build"
    for pth in ("/", "/neondb/rest/v1/", "/neondb/rest/v1/rpc/nonexistent_fn_probe"):
        conn = http.client.HTTPSConnection(DA, timeout=20, context=ctx)
        conn.request("GET", pth, headers={"Authorization": "Bearer " + jwt, "Accept": "application/json"})
        r = conn.getresponse()
        d = r.read().decode("utf-8", "replace")
        conn.close()
        out("C  GET %-40s -> %d %s" % (pth, r.status, d[:150]))
    # D. project_config dump
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s"
                 % (PROJ, BR),
                 headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    r = conn.getresponse()
    uri = json.loads(r.read().decode())["uri"]
    conn.close()
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    p = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
    uri2 = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
    import psycopg
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema='neon_auth' AND table_name='project_config'")
            cols = [x[0] for x in cur.fetchall()]
            out("D  project_config cols: %s" % cols)
            cur.execute("SELECT * FROM neon_auth.project_config")
            row = cur.fetchone()
            for c, v in zip(cols, row):
                s = str(v)
                out("D    %-20s = %s" % (c, s[:300]))
            # functions in public schema callable via rpc?
            cur.execute("SELECT p.proname, p.prosecdef, p.proacl IS NULL AS public_exec, "
                        "n.nspname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                        "WHERE n.nspname IN ('public','neon_auth') AND p.proacl IS NULL LIMIT 30")
            for row in cur.fetchall():
                out("D  fn: %s.%s definer=%s pub_exec=%s" % (row[3], row[0], row[1], row[2]))
    out("done")


if __name__ == "__main__":
    main()
