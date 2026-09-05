# -*- coding: utf-8 -*-
"""S2 diag: list branches both projects, retry create brB_tmp on PB"""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PB = "damp-term-63384673"
PBMAIN = "br-raspy-band-w247957z"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def call(method, path, body=None, timeout=30):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    conn.request(method, API_BASE + path, body=payload,
                 headers=dict(HB, Authorization="Bearer " + APIKEY,
                              **({"Content-Type": "application/json"} if body else {})))
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


for pid in (PA, PB):
    st, out = call("GET", "/projects/%s/branches" % pid)
    print("== branches %s -> %s" % (pid, st))
    for b in json.loads(out).get("branches", []):
        print("   ", b.get("id"), b.get("name"), "primary:", b.get("primary"),
              "state:", b.get("current_state"), "/", b.get("pending_state"))

st, out = call("POST", "/projects/%s/branches" % PB,
               {"branch": {"name": "s2-diag-b", "parent_id": PBMAIN}})
print("== create brB_tmp retry ->", st)
print(out[:1200])
