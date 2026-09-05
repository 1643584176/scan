# -*- coding: utf-8 -*-
"""diag: sign-in status for U1/U2/U3 + na2."""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()


def na(method, path, body=None, origin="http://localhost:3000", timeout=25):
    try:
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        hdrs = {"Content-Type": "application/json", "Origin": origin,
                "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        conn.request(method, path, json.dumps(body).encode() if body else None, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        time.sleep(0.5)
        return resp.status, data, ck
    except Exception as e:
        time.sleep(0.5)
        return None, str(e)[:150], ""


for email, pw in [("libobo1229+na_org1@gmail.com", "SecTest!2026pass"),
                  ("libobo1229+na_org2@gmail.com", "SecTest!2026pass"),
                  ("libobo1229+na2@gmail.com", "SecTest!2026pass2")]:
    st, d, ck = na("POST", "/neondb/auth/sign-in/email", {"email": email, "password": pw})
    print("%-38s -> %d %s ck=%s" % (email, st, d[:140], bool(ck)), flush=True)
