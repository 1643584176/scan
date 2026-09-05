# -*- coding: utf-8 -*-
"""Cleanup: delete stray orgs 5933d073 / 764274d1 (crashed V13 runs)."""
import json, ssl, time, http.client

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


def out(s):
    print(s, flush=True)


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=25):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        payload = json.dumps(body) if body is not None else None
        hdrs = {"Content-Type": "application/json", "Origin": origin,
                "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        if cookie:
            hdrs["Cookie"] = cookie
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.4)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.4)
        return None, str(e)[:120], ""


def fetch_db_uri():
    global DB_URI
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    conn.request("GET", API_BASE + "/projects/%s/connection_uri?database_name=neondb"
                 "&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN),
                 headers={"Authorization": "Bearer " + APIKEY})
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
    out("== cleanup stray orgs ==")
    fetch_db_uri()
    st, d, ck = na("POST", "/neondb/auth/sign-in/email",
                   {"email": "libobo1229+na_org1@gmail.com", "password": PASS})
    c1 = ck.split(";")[0] if st in (200, 201) else None
    out("cookie: %s" % bool(c1))
    if not c1:
        return
    for oid in ("5933d073-b997-4c32-bdda-f9f7f99e0f1c", "764274d1-43b1-4ebc-ae58-ea219d025ae9"):
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": oid}, c1)
        out("delete %s -> %d %s" % (oid, st, d[:80]))
    # any remaining v1x orgs
    r = dbq("SELECT id, name FROM neon_auth.organization WHERE name LIKE 'v1_-%'")
    out("remaining v1x orgs: %s" % r)
    for row in r or []:
        oid = str(row[0])
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": oid}, c1)
        out("delete %s (%s) -> %d" % (oid, row[1], st))
    # purge orphan invitations
    dbq("DELETE FROM neon_auth.invitation WHERE status='pending' AND email LIKE 'libobo1229+%'")
    out("purged orphan pending invites")
    r = dbq("SELECT id, name FROM neon_auth.organization WHERE name LIKE 'v1_-%'")
    out("after: %s" % r)
    out("done")


if __name__ == "__main__":
    main()
