# -*- coding: utf-8 -*-
"""diag2: find list-invitations path + accept with invitationId"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"


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


def auth(email):
    st, d, ck = na("POST", "/neondb/auth/sign-in/email", {"email": email, "password": PASS})
    return ck.split(";")[0] if st in (200, 201) else None


org = "cf373aa2-4548-41c6-9215-c9e66dc65360"
c1 = auth("libobo1229+na_org1@gmail.com")
c2 = auth("libobo1229+na_org2@gmail.com")
print("cookies", bool(c1), bool(c2))
for p in ("/neondb/auth/organization/list-invitations?organizationId=%s" % org,
          "/neondb/auth/organization/invitations/%s" % org,
          "/neondb/auth/organization/list-invitations",
          "/neondb/auth/organization/invitations"):
    st, d, _ = na("GET", p, cookie=c1)
    print("%-70s -> %d %s" % (p, st, d[:160]))
    if st == 200:
        break
