# -*- coding: utf-8 -*-
"""one-shot: delete stray org f3944ed3 + verify clean state."""
import json, ssl, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()
DB_URI = None
PASS = "SecTest!2026pass"


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=25):
    conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
    h = {"Content-Type": "application/json", "Origin": origin,
         "User-Agent": "Mozilla/5.0"}
    if cookie:
        h["Cookie"] = cookie
    conn.request(method, path, json.dumps(body).encode() if body else None, headers=h)
    r = conn.getresponse()
    d = r.read().decode("utf-8", "replace")
    ck = r.getheader("Set-Cookie", "")
    sc = r.status
    conn.close()
    return sc, d, ck


def fetch_db_uri():
    global DB_URI
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    conn.request("GET", API_BASE + "/projects/%s/connection_uri?database_name=neondb"
                 "&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN),
                 headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    resp = conn.getresponse()
    data = json.loads(resp.read().decode("utf-8", "replace"))
    conn.close()
    uri = data.get("uri")
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    parts = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    DB_URI = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def dbq(sql):
    import psycopg
    with psycopg.connect(DB_URI, connect_timeout=15) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description is None:
                return None
            return cur.fetchall()


def main():
    fetch_db_uri()
    st, d, ck = na("POST", "/neondb/auth/sign-in/email",
                   {"email": "libobo1229+na_org1@gmail.com", "password": PASS})
    c1 = ck.split(";")[0] if st in (200, 201) else None
    if not c1:
        print("no cookie")
        return
    for oid in ("f3944ed3-5976-4257-ac77-f9fe59820596",):
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": oid}, c1)
        print("del %s -> %d %s" % (oid, st, d[:60]))
        dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + oid + "'"))
        dbq('DELETE FROM neon_auth.member WHERE "organizationId"=%s' % ("'" + oid + "'"))
    r = dbq("SELECT id, name FROM neon_auth.organization WHERE name LIKE 'v2_-%' OR name LIKE 'v1_-%'")
    print("remaining test orgs:", r)
    dbq("DELETE FROM neon_auth.invitation WHERE status='pending' AND email LIKE 'libobo1229+%'")
    print("clean done")


if __name__ == "__main__":
    main()
