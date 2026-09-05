# -*- coding: utf-8 -*-
"""V37: verify-email precise loop - capture Location, test variants, check what actually verifies"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
NA = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
BASE = "/neondb/auth"
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"
EMAIL = "libobo1229+v37loop@gmail.com"
PASS = "SecTest!2026pass"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def req(method, p, body=None, cookie=None, raw=False):
    conn = http.client.HTTPSConnection(NA, timeout=25, context=ctx)
    h = {"Content-Type": "application/json", "Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"}
    if cookie:
        h["Cookie"] = cookie
    conn.request(method, BASE + "/" + p, json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    d = r.read().decode("utf-8", "replace")
    loc = r.getheader("Location", "")
    cks = r.headers.get_all("Set-Cookie") or []
    conn.close()
    if raw:
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
    out("== V37 ==")
    import psycopg
    conn = psycopg.connect(db_uri(), connect_timeout=15)
    conn.autocommit = True
    cur = conn.cursor()
    # fresh signup
    st, d, cks = req("POST", "sign-up/email", {"email": EMAIL, "password": PASS, "name": "v37loop"})
    out("signup -> %d" % st)
    cookie = "; ".join(c.split(";")[0] for c in cks)
    cur.execute("SELECT identifier, \"value\", \"expiresAt\" FROM neon_auth.verification "
                "WHERE identifier LIKE 'email-verification-otp%%' ORDER BY \"createdAt\" DESC LIMIT 2")
    rows = cur.fetchall()
    for r0 in rows:
        out("verif: id=%-70s exp=%s" % (r0[0], r0[1]))
    cur.execute("SELECT email, \"emailVerified\" FROM neon_auth.user WHERE email=%s", (EMAIL,))
    out("user: %s" % str(cur.fetchone()))
    tok = rows[0][1]
    # variant matrix with Location capture
    variants = [
        "verify-email?token=%s" % tok,
        "verify-email?token=%s&callbackURL=http://localhost:3000" % tok,
        "verify-email?token=%s&callbackURL=http%3A%2F%2Flocalhost%3A3000" % tok,
    ]
    for v in variants:
        st, d, loc, _ = req("GET", v, raw=True)
        out("GET %-80s -> %d loc=%s" % (v[:80], st, loc[:150]))
        time.sleep(0.5)
        cur.execute("SELECT \"emailVerified\" FROM neon_auth.user WHERE email=%s", (EMAIL,))
        out("   emailVerified now: %s" % str(cur.fetchone()[0]))
    # check verification rows after attempts (consumed?)
    cur.execute("SELECT identifier FROM neon_auth.verification WHERE identifier LIKE 'email-verification-otp%%'")
    out("remaining verif rows: %s" % str(cur.fetchall()))
    # is there a *token* based endpoint? check sign-in with unverified + check get-session claims
    st, d, _ = req("POST", "get-session", {}, cookie=cookie)
    out("get-session -> %d %s" % (st, d[:200]))
    # cleanup
    cur.execute("DELETE FROM neon_auth.session WHERE \"userId\" IN (SELECT id FROM neon_auth.user WHERE email=%s)", (EMAIL,))
    cur.execute("DELETE FROM neon_auth.verification WHERE identifier LIKE 'email-verification-otp%%'")
    cur.execute("DELETE FROM neon_auth.user WHERE email=%s", (EMAIL,))
    out("cleanup done; users left:")
    cur.execute("SELECT count(*) FROM neon_auth.user")
    out(str(cur.fetchone()[0]))
    conn.close()
    out("done")


if __name__ == "__main__":
    main()
