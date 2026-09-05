# -*- coding: utf-8 -*-
"""Quick PA branch listing with status codes."""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def call(method, path):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    conn.request(method, API_BASE + path,
                 headers=dict(HB, Authorization="Bearer " + APIKEY))
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


st, raw = call("GET", "/projects/orange-sun-90493739/branches")
print("PA list status:", st)
try:
    branches = json.loads(raw).get("branches", [])
    print("PA branches:", len(branches))
    for b in branches:
        print("   ", b.get("name"), b.get("id"), b.get("current_state"))
except Exception as e:
    print("parse err", e, raw[:400])
st, raw = call("GET", "/projects/orange-sun-90493739/branches/br-wandering-field-w2ob6mpn")
print("direct PA main GET:", st, raw[:200])
