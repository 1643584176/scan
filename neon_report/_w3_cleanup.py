# -*- coding: utf-8 -*-
"""Delete leftover branches from aborted W3 runs (w3src-* only)."""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def call(method, path, body=None):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    payload = json.dumps(body) if body is not None else None
    conn.request(method, API_BASE + path, body=payload,
                 headers=dict(HB, Authorization="Bearer " + APIKEY))
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


for proj in ("orange-sun-90493739", "damp-term-63384673"):
    st, raw = call("GET", "/projects/%s/branches" % proj)
    branches = json.loads(raw).get("branches", []) if st == 200 else []
    for b in branches:
        if b.get("name", "").startswith(("w3", "w3b")):
            s2, d2 = call("DELETE", "/projects/%s/branches/%s" % (proj, b["id"]))
            print("deleted", proj, b.get("name"), b["id"], "->", s2)
print("done")
