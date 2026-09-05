# -*- coding: utf-8 -*-
"""W4f: org matrix iter4 - member/admin ops against a REAL second member.
U1 owner, U2 & U3 members (both registered+joined), U4 spare.
Probes: member->member update/remove; admin->member update/remove; admin->owner guard.
X-Bug-Bounty: xxbo; DB read-only cross-check.
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
LOG = r"F:\scan\neon_report\_w4f_out.txt"
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"
U2 = "libobo1229+na_org2@gmail.com"
U3 = "libobo1229+na_org3@gmail.com"


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


def auth(email, fresh=False):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": PASS})
    if st in (200, 201):
        return ck.split(";")[0]
    if fresh:
        st, data, ck = na("POST", "/neondb/auth/sign-up/email",
                          {"email": email, "password": PASS, "name": "w4f-" + email[10:17]})
        if st in (200, 201):
            return ck.split(";")[0]
    return None


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
    out("%-42s -> %s %s" % (tag, st, data[:200]))
    return st, data


def main():
    out("== W4f matrix iter4 ==")
    if not fetch_db_uri():
        return
    c1 = auth(U1)
    c2 = auth(U2)
    c3 = auth(U3, fresh=True)
    out("sessions: U1=%s U2=%s U3=%s" % (bool(c1), bool(c2), bool(c3)))
    if not (c1 and c2 and c3):
        out("ABORT session fail")
        return
    st, data, _ = na("POST", "/neondb/auth/organization/create",
                     {"name": "w4f-org", "slug": "w4f-%d" % int(time.time())}, c1)
    org = json.loads(data).get("id") if st == 200 else None
    out("O3 = %s" % org)
    if not org:
        return
    # join U2 & U3 (invite by owner)
    for email, ck in ((U2, c2), (U3, c3)):
        st, data, _ = na("POST", "/neondb/auth/organization/invite-member",
                         {"organizationId": org, "email": email, "role": "member"}, c1)
        try:
            inv_id = json.loads(data).get("id")
        except Exception:
            inv_id = None
        if not inv_id:
            r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s '
                    'AND email=%s AND status=%s'
                    % ("'" + org + "'", "'" + email + "'", "'pending'"))
            inv_id = str(r[0][0]) if r else None
        if inv_id:
            st, data, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                             {"invitationId": inv_id}, ck)
            out("   join %s: %s" % (email, st))
    out("members: %s" % org_members(org))
    m2 = mid(org, U2)
    m3 = mid(org, U3)
    out("m2=%s m3=%s" % (m2, m3))

    # member(m2) -> member(m3)
    call("A member upd member role", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": m3, "role": "admin"}, c2)
    call("B member remove member", "POST",
         "/neondb/auth/organization/remove-member",
         {"organizationId": org, "memberIdOrEmail": m3}, c2)
    call("B2 member remove by email", "POST",
         "/neondb/auth/organization/remove-member",
         {"organizationId": org, "memberIdOrEmail": U3}, c2)
    out("members after member->member: %s" % org_members(org))

    # owner promotes U2 -> admin
    call("owner promote U2 admin", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": m2, "role": "admin"}, c1)
    out("members: %s" % org_members(org))
    # admin -> member
    call("C admin upd member role", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": m3, "role": "admin"}, c2)
    out("members after admin update: %s" % org_members(org))
    call("D admin remove member", "POST",
         "/neondb/auth/organization/remove-member",
         {"organizationId": org, "memberIdOrEmail": m3}, c2)
    out("members after admin remove: %s" % org_members(org))
    call("E admin remove owner", "POST",
         "/neondb/auth/organization/remove-member",
         {"organizationId": org, "memberIdOrEmail": mid(org, U1)}, c2)
    call("E2 admin upd owner role", "POST",
         "/neondb/auth/organization/update-member-role",
         {"organizationId": org, "memberId": mid(org, U1), "role": "member"}, c2)
    out("members after admin->owner probes: %s" % org_members(org))

    # cleanup
    call("cleanup delete O3", "POST", "/neondb/auth/organization/delete",
         {"organizationId": org}, c1)
    out("== W4f DONE")


if __name__ == "__main__":
    main()
