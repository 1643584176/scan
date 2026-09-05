# -*- coding: utf-8 -*-
"""V17: invitation cancel/reject endpoints x Origin matrix + state machine.
V15 showed cancel/reject return 400 (body) not 403 INVALID_ORIGIN anonymously
-> possibly missing Origin middleware (V13 CSRF matrix missed these two!).
Also: reject semantics, list-invitations visibility."""
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


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=25):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        payload = json.dumps(body) if body is not None else None
        hdrs = {"Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0", "Accept": "application/json",
                "X-Bug-Bounty": "xxbo"}
        if origin is not None:
            hdrs["Origin"] = origin
        if cookie:
            hdrs["Cookie"] = cookie
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.4)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.4)
        return None, str(e)[:120], ""


def auth(email, pw=PASS):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": pw})
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
    out("== V17 cancel/reject x Origin + state machine ==")
    fetch_db_uri()
    # cleanup stray orgs from crashed V13 run
    try:
        stray = dbq("SELECT id FROM neon_auth.organization WHERE name LIKE 'v13-%' OR name LIKE 'v14-%'")
        out("stray orgs: %s" % stray)
    except Exception as e:
        out("stray query err %s" % str(e)[:100])
    c1, c2, c3 = auth(U1), auth(U2), auth(U3)
    out("sessions: %s" % [bool(c1), bool(c2), bool(c3)])
    if not (c1 and c2 and c3):
        return
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v17-org", "slug": "v17-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    # U2 member, U3 invited pending
    na("POST", "/neondb/auth/organization/invite-member",
       {"organizationId": org, "email": U2, "role": "member"}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
    i2 = str(r[0][0]) if r else None
    if i2:
        na("POST", "/neondb/auth/organization/accept-invitation", {"invitationId": i2}, c2)
    na("POST", "/neondb/auth/organization/invite-member",
       {"organizationId": org, "email": U3, "role": "member"}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'" + U3 + "'", "'pending'"))
    i3 = str(r[0][0]) if r else None
    out("i3 (U3 pending): %s" % i3)
    if not i3:
        na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
        return

    # ---- list-invitations visibility ----
    for tag, cookie, qp in [("owner", c1, org), ("U3", c3, org)]:
        for qk in ("organizationId", "orgId"):
            st, d, _ = na("GET", "/neondb/auth/organization/list-invitations?%s=%s" % (qk, org),
                          cookie=cookie)
            if st == 200:
                out("list-inv %s(%s) -> 200 %s" % (tag, qk, d[:200]))
                break
        else:
            out("list-inv %s -> no 200 with either qk" % tag)

    # ---- cancel-invitation x Origin (owner U1) ----
    out("-- cancel-invitation (owner U1, i3) x Origin --")
    for tag, ov in [("ctrl-local", "http://localhost:3000"), ("evil.com", "https://evil.com"),
                    ("null", "null"), ("NO-Origin", None)]:
        st, d, _ = na("POST", "/neondb/auth/organization/cancel-invitation",
                      {"invitationId": i3}, c1, origin=ov)
        out("%-10s -> %d %s" % (tag, st, d[:110]))
        if st == 200 and ov != "http://localhost:3000":
            out("   !! cancel succeeded with %s" % tag)
    # after cancels, re-invite U3 for reject tests
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": U3, "role": "member"}, c1)
    out("re-invite U3 -> %d" % st)
    r = dbq('SELECT id, status FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'ORDER BY "createdAt" DESC LIMIT 1' % ("'" + org + "'", "'" + U3 + "'"))
    i3b, st3 = (str(r[0][0]), r[0][1]) if r else (None, None)
    out("latest U3 invite: %s status=%s" % (i3b, st3))
    if i3b:
        # reject by invitee U3 (ctrl origin first)
        st, d, _ = na("POST", "/neondb/auth/organization/reject-invitation",
                      {"invitationId": i3b}, c3)
        out("U3 reject (ctrl) -> %d %s" % (st, d[:110]))
        r = dbq('SELECT status FROM neon_auth.invitation WHERE id=%s' % ("'" + i3b + "'"))
        out("   status after reject: %s" % r)
        # can U3 still accept after reject?
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": i3b}, c3)
        out("U3 accept AFTER reject -> %d %s" % (st, d[:110]))
        # cross-user: U2 (member) tries to cancel U3's invite
        st, d, _ = na("POST", "/neondb/auth/organization/cancel-invitation",
                      {"invitationId": i3b}, c2)
        out("U2 member cancel U3 invite -> %d %s" % (st, d[:110]))
    # ---- reject-invitation x Origin (fresh invite) ----
    na("POST", "/neondb/auth/organization/invite-member",
       {"organizationId": org, "email": U3, "role": "member"}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s ORDER BY "createdAt" DESC LIMIT 1'
            % ("'" + org + "'", "'" + U3 + "'", "'pending'"))
    i3c = str(r[0][0]) if r else None
    if i3c:
        out("-- reject-invitation (U3 invitee) x Origin --")
        for tag, ov in [("ctrl-local", "http://localhost:3000"), ("evil.com", "https://evil.com"),
                        ("null", "null"), ("NO-Origin", None)]:
            st, d, _ = na("POST", "/neondb/auth/organization/reject-invitation",
                          {"invitationId": i3c}, c3, origin=ov)
            out("%-10s -> %d %s" % (tag, st, d[:110]))
            if st == 200 and ov != "http://localhost:3000":
                out("   !! reject succeeded with %s" % tag)
        # owner cancel x evil on fresh (if above consumed it, re-invite)
    # cleanup
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup delete -> %d" % st)
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
