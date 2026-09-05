# -*- coding: utf-8 -*-
"""Cleanup orphan temp branches from S2 first-run failure + S2b diag."""
import json
import time
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

ORPHANS = [
    ("orange-sun-90493739", "br-jolly-truth-w25q59a8"),   # s2-s282a6-a (first failed run)
    ("damp-term-63384673", "br-morning-field-w206bkb5"),  # s2-diag-b
]


def call(method, path, body=None, timeout=30):
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


for pid, bid in ORPHANS:
    st, out = call("DELETE", "/projects/%s/branches/%s" % (pid, bid))
    print("delete %s/%s -> %s %s" % (pid, bid, st, out[:150]), flush=True)
    time.sleep(2)

# verify clean
for pid in ("orange-sun-90493739", "damp-term-63384673"):
    st, out = call("GET", "/projects/%s/branches" % pid)
    print("== branches %s -> %s" % (pid, st))
    for b in json.loads(out).get("branches", []):
        print("   ", b.get("id"), b.get("name"), "primary:", b.get("primary"))
