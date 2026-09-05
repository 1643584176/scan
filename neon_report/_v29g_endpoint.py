# -*- coding: utf-8 -*-
"""V29g: create endpoint for v29iso branch -> READ-ONLY content check -> drop endpoint only"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-raspy-snow-w2n12fvw"


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


def main():
    out("== V29g endpoint + read-only ==")
    # create endpoint on the branch (compute only, no data change)
    st, d = api("POST", "/api/v2/projects/%s/endpoints" % PROJ,
                {"endpoint": {"branch_id": BR, "type": "read_write"}})
    out("create endpoint: %s" % st)
    if st >= 300:
        out(d[:300])
        return
    ep = json.loads(d)["endpoint"]
    epid = ep["id"]
    out("endpoint id: %s" % epid)
    # wait for ready
    for i in range(12):
        time.sleep(5)
        st, d = api("GET", "/api/v2/projects/%s/endpoints/%s" % (PROJ, epid))
        if st == 200:
            e = json.loads(d)["endpoint"]
            out("  endpoint state: %s" % e.get("state"))
            if e.get("state") == "active":
                break
    # read-only check
    st, d = api("GET", "/api/v2/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s"
                % (PROJ, BR))
    if st != 200:
        out("conn uri failed: %s %s" % (st, d[:200]))
    else:
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        u = urlsplit(json.loads(d)["uri"])
        q = [(k, v) for k, v in parse_qsl(u.query) if k != "channel_binding"]
        uri2 = urlunsplit((u.scheme, u.netloc, u.path, urlencode(q), u.fragment))
        import psycopg
        with psycopg.connect(uri2, connect_timeout=15) as dbc:
            dbc.autocommit = True
            with dbc.cursor() as cur:
                for t in ("user", "session", "account", "verification", "organization", "member", "invitation", "jwks"):
                    cur.execute("SELECT count(*) FROM neon_auth.%s" % t)
                    out("  neon_auth.%-14s %d rows" % (t, cur.fetchone()[0]))
                cur.execute("SELECT email FROM neon_auth.user ORDER BY \"createdAt\"")
                out("  users: %s" % [x[0] for x in cur.fetchall()])
                cur.execute("SELECT count(*) FROM neon_auth.project_config")
                out("  project_config: %d" % cur.fetchone()[0])
    # drop ONLY the endpoint (compute), keep branch intact
    st, d = api("DELETE", "/api/v2/projects/%s/endpoints/%s" % (PROJ, epid))
    out("drop endpoint: %s %s" % (st, d[:150]))
    out("done - branch untouched, only endpoint removed")


if __name__ == "__main__":
    main()
