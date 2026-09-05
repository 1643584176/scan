# -*- coding: utf-8 -*-
"""V31: recon - which attack surfaces are reachable on stage?
A. Buckets/Functions Beta endpoints (9/4 report named untested)
B. console auth-config endpoints (MCP tools: provision/update/get)
C. Data API: functions exposed via /rpc (platform functions?)
D. webhook config current state + enable path"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"
NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def api(method, path, body=None, host="console-stage.neon.build", extra=None):
    conn = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    if host == "console-stage.neon.build":
        h.update({"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    if extra:
        h.update(extra)
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    d = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, d


def main():
    out("== V31 recon ==")
    # A. Buckets / Functions endpoints
    for ep in ("buckets", "functions", "shared-functions", "neon_functions"):
        st, d = api("GET", "/api/v2/projects/%s/%s" % (PROJ, ep))
        out("A  GET projects/{p}/%-16s -> %d %s" % (ep, st, d[:90]))
    # B. auth config endpoints (console side)
    for ep in ("auth", "auth/config", "auth/configuration", "neon-auth", "neon_auth", "auth/enable",
               "auth/providers", "auth/jwks"):
        st, d = api("GET", "/api/v2/projects/%s/%s" % (PROJ, ep))
        out("B  GET projects/{p}/%-16s -> %d %s" % (ep, st, d[:90]))
    for ep in ("auth", "auth/config"):
        st, d = api("POST", "/api/v2/projects/%s/%s" % (PROJ, ep), {})
        out("B  POST projects/{p}/%-16s -> %d %s" % (ep, st, d[:90]))
    # branch-level auth endpoints
    st, d = api("GET", "/api/v2/projects/%s/branches/%s/auth" % (PROJ, BR))
    out("B  GET branches/{id}/auth          -> %d %s" % (st, d[:90]))
    # C. Data API function inventory
    st, d = api("GET", "/neondb/rest/v1/rpc/notexist_probe", host="ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build")
    out("C  DataAPI rpc probe -> %d %s" % (st, d[:120]))
    # D. project_config webhook state (DB)
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
                out("D    %-20s = %s" % (c, s[:200]))
    out("done")


if __name__ == "__main__":
    main()
