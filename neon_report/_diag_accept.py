# -*- coding: utf-8 -*-
"""diag: U2 accept 400 reason - pending invites, error body, list state"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"
U2 = "libobo1229+na_org2@gmail.com"


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=25):
    conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
    hdrs = {"Content-Type": "application/json", "Origin": origin,
            "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    if cookie:
        hdrs["Cookie"] = cookie
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    ck = resp.getheader("Set-Cookie", "")
    conn.close()
    time.sleep(0.3)
    return resp.status, data, ck


st, d, ck = na("POST", "/neondb/auth/sign-in/email", {"email": U2, "password": PASS})
print("U2 sign-in %d" % st)
c2 = ck.split(";")[0]
org = "cf373aa2-4548-41c6-9215-c9e66dc65360"
# 1. error body of accept
st, d, _ = na("POST", "/neondb/auth/organization/accept-invitation", {"organizationId": org}, c2)
print("accept -> %d %s" % (st, d[:250]))
# 2. U2 org list (member count?)
st, d, _ = na("GET", "/neondb/auth/organization/list", cookie=c2)
print("U2 list -> %d %s" % (st, d[:300]))
# 3. U2 pending invites? (list-invitations needs membership; try anyway)
st, d, _ = na("GET", "/neondb/auth/organization/invitations?organizationId=%s" % org, cookie=c2)
print("U2 invites -> %d %s" % (st, d[:250]))
# 4. U1 view of the invite status
st, d, c1 = na("POST", "/neondb/auth/sign-in/email", {"email": "libobo1229+na_org1@gmail.com", "password": PASS})
c1 = c1.split(";")[0]
st, d, _ = na("GET", "/neondb/auth/organization/invitations?organizationId=%s" % org, cookie=c1)
print("U1 invites -> %d %s" % (st, d[:400]))
