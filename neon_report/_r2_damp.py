# -*- coding: utf-8 -*-
"""Recon2: damp-term auth integration + endpoints + branches; compare with A."""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


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


for pid in ("damp-term-63384673", "orange-sun-90493739"):
    st, out = call("GET", "/projects/%s/auth/integrations" % pid)
    print("== auth integrations %s -> %s" % (pid, st))
    print("   ", out[:800])
    st, out = call("GET", "/projects/%s/branches" % pid)
    print("== branches %s -> %s" % (pid, st))
    if st == 200:
        for b in json.loads(out).get("branches", []):
            print("   branch:", b.get("id"), b.get("name"), "primary:", b.get("primary"),
                  "created:", b.get("created_at"))
    st, out = call("GET", "/projects/%s/endpoints" % pid)
    print("== endpoints %s -> %s" % (pid, st))
    if st == 200:
        for e in json.loads(out).get("endpoints", []):
            print("   ep:", e.get("id"), "branch:", e.get("branch_id"),
                  "host:", e.get("host"), "created:", e.get("created_at"))
    st, out = call("GET", "/projects/%s/branches/%s/databases" % pid,
                   ) if False else (None, None)
    if st:
        print("   dbs:", out[:400])
