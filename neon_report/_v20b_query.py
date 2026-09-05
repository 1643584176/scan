# -*- coding: utf-8 -*-
"""V20b: query-variant + cleanup org 5f950952 (V20 crashed before cleanup)."""
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


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=25):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        payload = json.dumps(body) if body is not None else None
        hdrs = {"Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        if origin is not None:
            hdrs["Origin"] = origin
        if cookie:
            hdrs["Cookie"] = cookie
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
    out("== V20b query variant + cleanup ==")
    fetch_db_uri()
    c1 = auth(U1)
    if not c1:
        return
    # find v20 org
    r = dbq("SELECT id FROM neon_auth.organization WHERE name LIKE 'v20-%'")
    for row in r or []:
        oid = str(row[0])
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": oid}, c1)
        out("del v20 org %s -> %d" % (oid, st))
        dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + oid + "'"))
        dbq('DELETE FROM neon_auth.member WHERE "organizationId"=%s' % ("'" + oid + "'"))
    # create fresh for query test
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v20b", "slug": "v20b%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    body = {"organizationId": org, "email": "libobo1229+v20b%s@gmail.com" % (str(int(time.time()))[-6:]),
            "role": "member"}
    base = "/neondb/auth/organization/invite-member"
    # query variant: query stripped by router -> canonical handler + origin check?
    st, d, _ = na("POST", base + "?x=1", body, c1, origin=None)
    out("query no-origin -> %d %s" % (st, d[:110]))
    st, d, _ = na("POST", base + "?x=1", body, c1, origin="http://localhost:3000")
    out("query +origin   -> %d %s" % (st, d[:110]))
    # %2e + no origin ctrl (already known 403)
    st, d, _ = na("POST", "/neondb/auth/organization/./invite-member", body, c1, origin=None)
    out("%2e no-origin   -> %d %s" % (st, d[:110]))
    # cleanup
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup -> %d" % st)
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    dbq('DELETE FROM neon_auth.member WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
