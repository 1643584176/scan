# -*- coding: utf-8 -*-
"""V5b: verification endpoint hunt + signup duplicate/case semantics.
Hypothesis: (a) verify endpoint exists at non-standard path w/o rate limit -> OTP brute;
(b) signup accepts existing/uppercase email -> identity confusion/pre-registration."""
import json, ssl, time, http.client, random, string

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
TAG = "v5b" + "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
NEW = "libobo1229+%s@gmail.com" % TAG
EXIST = "libobo1229+na_org1@gmail.com"   # already registered
UPPER = "LIBOBO1229+%s@gmail.com" % TAG  # case variant of NEW


def na(method, path, body=None, cookie=None, timeout=25):
    conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = {"Content-Type": "application/json", "Origin": "http://localhost:3000",
            "User-Agent": "Mozilla/5.0", "Accept": "application/json", "X-Bug-Bounty": "xxbo"}
    if cookie:
        hdrs["Cookie"] = cookie
    t0 = time.time()
    conn.request(method, path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    ck = resp.getheader("Set-Cookie", "")
    dt = time.time() - t0
    conn.close()
    time.sleep(0.5)
    return resp.status, data, ck, dt


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def main():
    out("== V5b ==")
    # signup fresh
    st, d, ck, dt = na("POST", "/neondb/auth/sign-up/email",
                       {"email": NEW, "password": "SecTest!2026pass", "name": TAG})
    out("fresh signup %s -> %d %s" % (NEW, st, d[:160]))
    cookie = ck.split(";")[0] if ck else ""
    # (b1) signup with EXISTING email
    st, d, _, dt = na("POST", "/neondb/auth/sign-up/email",
                      {"email": EXIST, "password": "SecTest!2026pass", "name": "dup"})
    out("dup signup(existing) -> %d %s" % (st, d[:200]))
    # (b2) sign-in with wrong password on existing -> compare error (enumeration?)
    st, d, _, dt = na("POST", "/neondb/auth/sign-in/email",
                      {"email": EXIST, "password": "WrongPass!1"})
    out("signin wrongpw -> %d %s" % (st, d[:200]))
    st, d, _, dt = na("POST", "/neondb/auth/sign-in/email",
                      {"email": "nobody-%s@gmail.com" % TAG, "password": "WrongPass!1"})
    out("signin no-user -> %d %s" % (st, d[:200]))
    # (b3) case variant signup
    st, d, _, dt = na("POST", "/neondb/auth/sign-up/email",
                      {"email": UPPER, "password": "SecTest!2026pass", "name": "upper"})
    out("upper signup -> %d %s" % (st, d[:200]))
    # (b4) verify endpoint path hunt (POST + GET)
    cands = ["verify-email", "email-verification", "verify", "verification",
             "verify-email/otp", "otp/verify", "email/verify", "verify-otp"]
    for c in cands:
        for m in ("POST",):
            st, d, _, dt = na(m, "/neondb/auth/" + c,
                              {"email": NEW, "code": "123456"}, cookie or None)
            mark = "!!" if st not in (404, 405) else "  "
            out("%s %s /neondb/auth/%s -> %d %s" % (mark, m, c, st, d[:130]))
    # forgot-password flow presence
    for c in ("forget-password", "forgot-password", "request-password-reset",
              "reset-password", "send-password-reset-email"):
        st, d, _, dt = na("POST", "/neondb/auth/" + c, {"email": NEW}, cookie or None)
        mark = "!!" if st not in (404, 405) else "  "
        out("%s POST /neondb/auth/%s -> %d %s" % (mark, c, st, d[:130]))


if __name__ == "__main__":
    main()
