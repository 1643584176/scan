# -*- coding: utf-8 -*-
"""V19b: reject-invitation cross-identity (missed in V19: invitee was already member)
+ cleanup stray v9-org."""
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
U2 = "libobo1229+na_org2@gmail.com"
U3 = "libobo1229+na_org3@gmail.com"


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
        time.sleep(0.4)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.4)
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
    out("== V19b reject cross-identity + stray cleanup ==")
    fetch_db_uri()
    c1, c2, c3 = auth(U1), auth(U2), auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not (c1 and c2 and c3):
        return
    # org C owned by U1; invite U2 (U2 unrelated to C as non-member... U2 not member yet)
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v19c", "slug": "v19c%d" % int(time.time())}, c1)
    orgC = json.loads(d).get("id") if st == 200 else None
    out("orgC=%s" % orgC)
    if not orgC:
        return
    na("POST", "/neondb/auth/organization/invite-member",
       {"organizationId": orgC, "email": U2, "role": "member"}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + orgC + "'", "'" + U2 + "'", "'pending'"))
    iC2 = str(r[0][0]) if r else None
    out("invite U2->C: %s" % iC2)
    if iC2:
        # U3 (unrelated to orgC, not recipient) tries reject
        st, d, _ = na("POST", "/neondb/auth/organization/reject-invitation",
                      {"invitationId": iC2}, c3)
        out("U3 reject U2's invite -> %d %s" % (st, d[:150]))
        r = dbq('SELECT status FROM neon_auth.invitation WHERE id=%s' % ("'" + iC2 + "'"))
        out("   status: %s" % r)
        # U2 (recipient, unrelated org member) reject own - should work
        st, d, _ = na("POST", "/neondb/auth/organization/reject-invitation",
                      {"invitationId": iC2}, c2)
        out("U2 reject own (ctrl)  -> %d %s" % (st, d[:150]))
        r = dbq('SELECT status FROM neon_auth.invitation WHERE id=%s' % ("'" + iC2 + "'"))
        out("   status: %s" % r)
    # cleanup orgC + stray v9-org
    for oid in (orgC,):
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": oid}, c1)
        out("del orgC -> %d" % st)
    r = dbq("SELECT id FROM neon_auth.organization WHERE name LIKE 'v9-%' OR name LIKE 'v1_-%'")
    out("stray v9/v1x orgs: %s" % r)
    for row in r or []:
        oid = str(row[0])
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": oid}, c1)
        out("del stray %s -> %d" % (oid, st))
    dbq("DELETE FROM neon_auth.invitation WHERE status='pending' AND email LIKE 'libobo1229+%'")
    out("done")


if __name__ == "__main__":
    main()
