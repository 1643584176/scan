# -*- coding: utf-8 -*-
"""W4b: Neon Auth plugin surface - configs + better-auth org plugin routes.
1) control plane: GET auth/plugins* on PA main
2) NA (better-auth) org plugin route reachability with a real session
   (self-created na users only; X-Bug-Bounty: xxbo)
"""
import json
import ssl
import time
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo", "Content-Type": "application/json"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
LOG = r"F:\scan\neon_report\_w4b_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def out(s):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), s)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def api(method, path, body=None):
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
        payload = json.dumps(body) if body is not None else None
        conn.request(method, API_BASE + path, body=payload,
                     headers=dict(HB, Authorization="Bearer " + APIKEY))
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        conn.close()
        return resp.status, data
    except Exception as e:
        return None, str(e)[:150]


def na(method, path, body=None, cookie=None, timeout=30):
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
        payload = json.dumps(body) if body is not None else None
        hdrs = {"Content-Type": "application/json", "Origin": "http://localhost:3000",
                "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        if cookie:
            hdrs["Cookie"] = cookie
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        cookie_new = resp.getheader("Set-Cookie", "")
        conn.close()
        return resp.status, data, cookie_new
    except Exception as e:
        return None, str(e)[:150], ""


def main():
    out("== W4b auth plugins recon ==")
    # ---- 1. control-plane plugin configs ----
    st, raw = api("GET", "/projects/%s/branches/%s/auth/plugins" % (PA, PAMAIN))
    out("plugins: %s %s" % (st, raw[:800]))
    for plug in ("organization", "phone-number", "magic-link"):
        st, raw = api("GET", "/projects/%s/branches/%s/auth/plugins/%s" % (PA, PAMAIN, plug))
        out("plugin %-14s: %s %s" % (plug, st, raw[:400]))

    # ---- 2. NA org routes with fresh session ----
    email = "libobo1229+na_org1@gmail.com"
    st, data, ck = na("POST", "/neondb/auth/sign-up/email",
                      {"email": email, "password": "SecTest!2026pass", "name": "w4b-user"})
    out("sign-up %s: %s %s" % (email, st, data[:200]))
    if st not in (200, 201):
        st, data, ck = na("POST", "/neondb/auth/sign-in/email",
                          {"email": email, "password": "SecTest!2026pass"})
        out("sign-in: %s %s" % (st, data[:200]))
    sess = ""
    if ck:
        sess = ck.split(";")[0]
    out("session cookie: %s" % (sess[:60] if sess else "NONE"))
    if not sess:
        out("ABORT no session")
        return
    # org plugin routes (better-auth convention)
    for path in ["/neondb/auth/organization/list",
                 "/neondb/auth/organization/create",
                 "/neondb/auth/organization/members",
                 "/neondb/auth/organization"]:
        if path.endswith("create"):
            st, data, _ = na("POST", path, {"name": "w4b-org", "slug": "w4b-org-%d" % int(time.time())}, sess)
        else:
            st, data, _ = na("GET", path, None, sess)
        out("NA %-42s -> %s %s" % (path, st, data[:250]))
    out("== W4b DONE")


if __name__ == "__main__":
    main()
