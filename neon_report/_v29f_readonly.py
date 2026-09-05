# -*- coding: utf-8 -*-
"""V29f: READ-ONLY check of v29iso branch contents (no writes, no drops)
then report. Branch deletion decision left to user if contents uncertain."""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-raspy-snow-w2n12fvw"  # v29iso branch created moments ago


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
    out("== V29f read-only branch contents check ==")
    # 1. does branch exist + its metadata
    st, d = api("GET", "/api/v2/projects/%s/branches/%s" % (PROJ, BR))
    out("branch meta: %s" % st)
    if st == 200:
        b = json.loads(d)["branch"]
        out("  name=%s parent=%s created=%s" % (b.get("name"), b.get("parent_id"), b.get("created_at")))
    # 2. connect read-only and count/compare
    st, d = api("GET", "/api/v2/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s"
                % (PROJ, BR))
    if st != 200:
        out("conn uri failed: %s %s" % (st, d[:200]))
        return
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
            users = [x[0] for x in cur.fetchall()]
            out("  users(%d): %s" % (len(users), users))
            cur.execute("SELECT \"projectId\" IS NOT NULL, count(*) FROM neon_auth.project_config GROUP BY 1")
            out("  project_config rows: %s" % cur.fetchall())
    # 3. main branch same tables for comparison (read-only)
    st, d = api("GET", "/api/v2/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s"
                % (PROJ, "br-wandering-field-w2ob6mpn"))
    u = urlsplit(json.loads(d)["uri"])
    q = [(k, v) for k, v in parse_qsl(u.query) if k != "channel_binding"]
    uri3 = urlunsplit((u.scheme, u.netloc, u.path, urlencode(q), u.fragment))
    with psycopg.connect(uri3, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT count(*) FROM neon_auth.user")
            out("  MAIN branch users: %d" % cur.fetchone()[0])
    out("done - no writes performed")


if __name__ == "__main__":
    main()
