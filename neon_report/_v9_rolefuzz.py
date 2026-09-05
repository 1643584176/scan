# -*- coding: utf-8 -*-
"""V9: role-value boundary fuzz + owner state machine edge cases.
- update-member-role with non-whitelist role values (OWNER/''/SuperAdmin/whitespace)
- invite-member role fuzz same set
- single-owner leave / self remove-member / dual-owner leave semantics
Checks: whitelist enforcement, DB role pollution, orphan-org possibility."""
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
    out("== V9 role fuzz + owner edge ==")
    fetch_db_uri()
    c1, c2, c3 = auth(U1), auth(U2), auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not all([c1, c2, c3]):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v9-org", "slug": "v9-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return

    # F1: invite role fuzz (owner invites)
    for rv in ["OWNER", "owner ", " owner", "SuperAdmin", "superadmin", "", "admin", "member"]:
        st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                      {"organizationId": org, "email": U2, "role": rv}, c1)
        out("F1 invite role=%-12r -> %d %s" % (rv, st, d[:110]))

    # F2: U2 joins as member normally, then update-role fuzz by owner
    i = None
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND role=%s AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'member'", "'pending'"))
    if r:
        i = str(r[0][0])
    if not i:
        st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                      {"organizationId": org, "email": U2, "role": "member"}, c1)
        i = json.loads(d).get("id")
    st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                  {"invitationId": i}, c2)
    out("U2 joined: %d" % st)
    m2 = mid(org, U2)
    for rv in ["OWNER", "owner ", " owner", "SuperAdmin", "superadmin", "", "ADMIN", "member"]:
        st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                      {"organizationId": org, "memberId": m2, "role": rv}, c1)
        out("F2 update role=%-12r -> %d %s" % (rv, st, d[:110]))
        r = dbq('SELECT role FROM neon_auth.member WHERE id=%s' % ("'" + m2 + "'"))
        out("      db role now: %s" % r)

    # F3: single-owner leave attempt (org has 1 owner U1)
    st, d, _ = na("POST", "/neondb/auth/organization/leave",
                  {"organizationId": org}, c1)
    out("F3 single-owner U1 leave  -> %d %s" % (st, d[:130]))
    # F4: owner self-remove-member
    m1 = mid(org, U1)
    st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                  {"organizationId": org, "memberIdOrEmail": m1}, c1)
    out("F4 single-owner self-remove -> %d %s" % (st, d[:130]))
    r = members(org)
    out("   members after F3/F4: %s" % r)

    # F5: dual-owner then owner leave (state machine: leave while other owner exists)
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": U2, "role": "owner"}, c1)
    i2 = json.loads(d).get("id") if st == 200 else None
    if i2:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": i2}, c2)
        out("U2 became owner: %d" % st)
        st, d, _ = na("POST", "/neondb/auth/organization/leave",
                      {"organizationId": org}, c1)
        out("F5 U1(owner) leave w/ U2 owner -> %d %s" % (st, d[:130]))
        r = members(org)
        out("   members after F5: %s" % r)
        # remaining owner U2 deletes org
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c2)
        out("cleanup U2 deletes org -> %d" % st)
    else:
        dbq('DELETE FROM neon_auth.member WHERE "organizationId"=%s' % ("'" + org + "'"))
        st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
        out("cleanup (fallback) delete org -> %d" % st)
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
