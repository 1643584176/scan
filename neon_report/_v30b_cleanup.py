# -*- coding: utf-8 -*-
"""V30b: cleanup v30 sign-up users + verify no branches left"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def api(method, path, body=None):
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    h = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY,
         "Content-Type": "application/json"}
    conn.request(method, path, json.dumps(body).encode() if body else None, headers=h)
    r = conn.getresponse()
    d = r.read().decode()
    conn.close()
    return r.status, d


def main():
    out("== V30b cleanup ==")
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/%s/connection_uri?database_name=neondb"
                 "&role_name=neondb_owner&branch_id=br-wandering-field-w2ob6mpn" % PROJ,
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
            cur.execute("SELECT id FROM neon_auth.user WHERE email LIKE 'libobo1229+v30%%' OR email LIKE 'libobo1229+v30b%%'")
            ids = [x[0] for x in cur.fetchall()]
            out("v30 users to delete: %d" % len(ids))
            for uid in ids:
                cur.execute("DELETE FROM neon_auth.session WHERE \"userId\"=%s", (uid,))
                cur.execute("DELETE FROM neon_auth.account WHERE \"userId\"=%s", (uid,))
                cur.execute("DELETE FROM neon_auth.user WHERE id=%s", (uid,))
            cur.execute("SELECT count(*) FROM neon_auth.user")
            out("users now: %d" % cur.fetchone()[0])
    # branches check
    st, d = api("GET", "/api/v2/projects/%s/branches" % PROJ)
    branches = json.loads(d)["branches"]
    out("branches now: %d" % len(branches))
    for b in branches:
        out("  %s %s" % (b["id"], b.get("name")))
    out("done")


if __name__ == "__main__":
    main()
