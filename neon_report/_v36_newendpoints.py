# -*- coding: utf-8 -*-
"""V36: probe new endpoints
1. refresh-token semantics (providerId variants, with/without cookie)
2. email verification full loop: signup v36 user -> request-email-verification -> OTP from DB -> verify-email
3. callback/google 302 target + error flows"""
import json, ssl, time, http.client, re

ctx = ssl.create_default_context()
NA = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
BASE = "/neondb/auth"
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"
EMAIL = "libobo1229+v36loop@gmail.com"
PASS = "SecTest!2026pass"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def req(method, p, body=None, cookie=None, getloc=False, extra=None):
    conn = http.client.HTTPSConnection(NA, timeout=25, context=ctx)
    h = {"Content-Type": "application/json", "Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"}
    if cookie:
        h["Cookie"] = cookie
    if extra:
        h.update(extra)
    conn.request(method, BASE + "/" + p, json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    d = r.read().decode("utf-8", "replace")
    loc = r.getheader("Location", "")
    cks = r.headers.get_all("Set-Cookie") or []
    conn.close()
    if getloc:
        return r.status, d, loc, cks
    return r.status, d, cks


def db_uri():
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
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


def main():
    out("== V36 ==")
    # 1. sign in U1 for authed probes
    st, d, cks = req("POST", "sign-in/email", {"email": "libobo1229+na_org1@gmail.com", "password": PASS})
    cookie = "; ".join(c.split(";")[0] for c in cks)
    out("signin -> %d" % st)
    # 1a. refresh-token without providerId / with variants
    for body in ({}, {"providerId": "google"}, {"providerId": "credential"}, {"providerId": "email"},
                 {"providerId": "google", "refreshToken": "x"}):
        st, d, _ = req("POST", "refresh-token", body, cookie=cookie)
        out("refresh-token %-55s -> %d %s" % (json.dumps(body), st, d[:100]))
        time.sleep(0.2)
    # 1b. new endpoints with session
    for p, body in (("list-sessions", None), ("change-password", {"newPassword": "X"}),
                    ("change-email", {"newEmail": "libobo1229+v36chg@gmail.com"}),
                    ("revoke-other-sessions", None), ("list-accounts", None)):
        st, d, _ = req("GET" if body is None and p in ("list-sessions", "list-accounts") else "POST",
                       p, body if body is not None else ({} if "GET" != "GET" else None), cookie=cookie)
        out("%-22s -> %d %s" % (p, st, d[:110]))
        time.sleep(0.2)
    # 2. email verification loop with fresh user
    st, d, cks = req("POST", "sign-up/email", {"email": EMAIL, "password": PASS, "name": "v36loop"})
    out("signup -> %d %s" % (st, d[:100]))
    st, d, _ = req("POST", "request-email-verification", {"email": EMAIL})
    out("request-email-verification -> %d %s" % (st, d[:100]))
    time.sleep(1)
    import psycopg
    with psycopg.connect(db_uri(), connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT \"value\", \"expiresAt\" FROM neon_auth.verification WHERE identifier LIKE 'email-verification-otp%%' ORDER BY \"createdAt\" DESC LIMIT 3")
            rows = cur.fetchall()
            for r0 in rows:
                out("verification row: id=%s exp=%s" % (r0[0], r0[1]))
            cur.execute("SELECT email, \"emailVerified\" FROM neon_auth.user WHERE email=%s", (EMAIL,))
            out("user row: %s" % str(cur.fetchone()))
    otp = None
    with psycopg.connect(db_uri(), connect_timeout=15) as dbc:
        with dbc.cursor() as cur:
            cur.execute("SELECT \"value\" FROM neon_auth.verification WHERE identifier LIKE 'email-verification-otp%%' ORDER BY \"createdAt\" DESC LIMIT 1")
            r0 = cur.fetchone()
            otp = r0[0] if r0 else None
    out("otp: %s" % otp)
    if otp:
        st, d, _ = req("GET", "verify-email?token=%s&callbackURL=http://localhost:3000" % otp)
        out("verify-email GET -> %d %s" % (st, d[:120]))
        time.sleep(1)
        with psycopg.connect(db_uri(), connect_timeout=15) as dbc:
            dbc.autocommit = True
            with dbc.cursor() as cur:
                cur.execute("SELECT email, \"emailVerified\" FROM neon_auth.user WHERE email=%s", (EMAIL,))
                out("after verify: %s" % str(cur.fetchone()))
        # reuse same OTP?
        st, d, _ = req("GET", "verify-email?token=%s&callbackURL=http://localhost:3000" % otp)
        out("verify-email REUSE -> %d %s" % (st, d[:120]))
    # 3. callback 302 targets
    for prov in ("google", "github"):
        st, d, loc, _ = req("GET", "callback/%s" % prov, getloc=True)
        out("callback/%s -> %d loc=%s" % (prov, st, loc[:120]))
        time.sleep(0.3)
    # cleanup v36 user
    with psycopg.connect(db_uri(), connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("DELETE FROM neon_auth.session WHERE \"userId\" IN (SELECT id FROM neon_auth.user WHERE email=%s)", (EMAIL,))
            cur.execute("DELETE FROM neon_auth.verification WHERE identifier LIKE '%%v36%%' OR identifier LIKE 'email-verification-otp%%'")
            cur.execute("DELETE FROM neon_auth.user WHERE email=%s", (EMAIL,))
            out("cleanup done")
    out("done")


if __name__ == "__main__":
    main()
