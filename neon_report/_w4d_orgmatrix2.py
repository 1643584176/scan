# -*- coding: utf-8 -*-
"""W4d: org matrix iteration 2 - accept invite, then member-level privilege probes.
DB (neon_auth schema on our own branch) used ONLY as read-only cross-check.
U1=owner(O1), U2=invitee. Self-created data; X-Bug-Bounty: xxbo.
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
DB_URI = None   # fetched at runtime (password rotates)
LOG = r"F:\scan\neon_report\_w4d_out.txt"
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"
U2 = "libobo1229+na_org2@gmail.com"
O1 = "3189832e-d87e-436b-8a47-a8e09a33deb6"


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


def fetch_db_uri():
    """Get current role password via control plane (password rotates)."""
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
        if not uri:
            return False
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        parts = urlsplit(uri)
        q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
        DB_URI = urlunsplit((parts.scheme, parts.netloc, parts.path,
                             urlencode(q), parts.fragment))
        return True
    except Exception as e:
        out("fetch uri err: %s" % str(e)[:150])
        return False


def dbq(sql):
    import psycopg
    with psycopg.connect(DB_URI, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def members_db():
    return dbq('SELECT id, "organizationId", "userId", role FROM neon_auth.member '
               'WHERE "organizationId"=%s ORDER BY "createdAt"' % ("'" + O1 + "'"))


def call(tag, method, path, body, cookie, full=False):
    st, data, _ = na(method, path, body, cookie)
    out("%-36s -> %s %s" % (tag, st, data[:600 if full else 220]))
    return st, data


def main():
    out("== W4d matrix iter2 ==")
    if not fetch_db_uri():
        out("ABORT no db uri")
        return
    c1 = signin(U1)
    c2 = signin(U2)
    out("sessions: U1=%s U2=%s" % (bool(c1), bool(c2)))
    if not c1 or not c2:
        return

    # ---- 0. state ----
    out("DB members now: %s" % members_db())
    invs = dbq('SELECT id, email, role, status FROM neon_auth.invitation '
               'WHERE "organizationId"=%s ORDER BY "createdAt"' % ("'" + O1 + "'"))
    out("DB invitations now: %s" % invs)
    inv_id = None
    if invs:
        row = [r for r in invs if r[1] == U2]
        if row:
            inv_id = row[0][0]

    # ---- 1. invite (full response; reuse pending if exists) ----
    if not inv_id:
        st, data, _ = na("POST", "/neondb/auth/organization/invite-member",
                         {"organizationId": O1, "email": U2, "role": "member"}, c1)
        out("invite fresh: %s %s" % (st, data[:600]))
        try:
            inv_id = json.loads(data).get("id")
        except Exception:
            pass
    out("invitation id: %s" % inv_id)

    # ---- 2. U2 accepts ----
    if inv_id:
        call("U2 accept-invitation", "POST",
             "/neondb/auth/organization/accept-invitation",
             {"invitationId": str(inv_id)}, c2, full=True)
    out("DB members after accept: %s" % members_db())
    # member ids via DB cross-check
    u2_uid = dbq('SELECT id FROM neon_auth.user WHERE email=%s' % ("'" + U2 + "'"))
    u1_uid = dbq('SELECT id FROM neon_auth.user WHERE email=%s' % ("'" + U1 + "'"))
    out("uids: U2=%s U1=%s" % (u2_uid, u1_uid))
    u2_mid = u1_mid = None
    if u2_uid:
        u2_mid = dbq('SELECT id FROM neon_auth.member WHERE "organizationId"=%s '
                     'AND "userId"=%s' % ("'" + O1 + "'", "'" + str(u2_uid[0][0]) + "'"))
    if u1_uid:
        u1_mid = dbq('SELECT id FROM neon_auth.member WHERE "organizationId"=%s '
                     'AND "userId"=%s' % ("'" + O1 + "'", "'" + str(u1_uid[0][0]) + "'"))
    out("member ids: U2=%s U1=%s" % (u2_mid, u1_mid))

    # ---- 3. member-level escalation probes (U2) ----
    if u2_mid:
        call("E1a promote self by memberId", "POST",
             "/neondb/auth/organization/update-member-role",
             {"organizationId": O1, "memberId": str(u2_mid[0][0]), "role": "owner"}, c2)
        call("E1b promote self by email", "POST",
             "/neondb/auth/organization/update-member-role",
             {"organizationId": O1, "memberIdOrEmail": U2, "role": "owner"}, c2)
        call("E2 remove owner by email", "POST",
             "/neondb/auth/organization/remove-member",
             {"organizationId": O1, "memberIdOrEmail": U1}, c2)
        call("E3 delete org as member", "POST",
             "/neondb/auth/organization/delete", {"organizationId": O1}, c2)
        call("E4 leave org as member", "POST",
             "/neondb/auth/organization/leave", {"organizationId": O1}, c2)
    out("DB members after U2 probes: %s" % members_db())

    # ---- 4. owner controls (U1) ----
    if u2_mid:
        call("ctrl U1 promote U2 admin", "POST",
             "/neondb/auth/organization/update-member-role",
             {"organizationId": O1, "memberIdOrEmail": U2, "role": "admin"}, c1)
        out("DB members after owner op: %s" % members_db())
        call("ctrl U1 demote U2 member", "POST",
             "/neondb/auth/organization/update-member-role",
             {"organizationId": O1, "memberIdOrEmail": U2, "role": "member"}, c1)
    # ---- 5. leave as member (U2) & owner cleanup ----
    call("U2 leave (member)", "POST",
         "/neondb/auth/organization/leave", {"organizationId": O1}, c2)
    out("DB members after U2 leave: %s" % members_db())
    call("U1 delete O1 cleanup", "POST",
         "/neondb/auth/organization/delete", {"organizationId": O1}, c1)
    out("== W4d DONE")


if __name__ == "__main__":
    main()
