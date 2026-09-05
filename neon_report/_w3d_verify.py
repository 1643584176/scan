# -*- coding: utf-8 -*-
"""Verify: does PB still have the w3dtmp branch after cross-path DELETE attempt?"""
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


for proj, tag in (("orange-sun-90493739", "PA"), ("damp-term-63384673", "PB")):
    st, raw = call("GET", "/projects/%s/branches" % proj)
    branches = json.loads(raw).get("branches", []) if st == 200 else []
    print(tag, "branches:")
    for b in branches:
        print("   ", b.get("name"), b.get("id"), b.get("current_state"), b.get("pending_state"))
# direct GET of the w3dtmp id
st, raw = call("GET", "/projects/%s/branches/br-billowing-shape-w2c8b1x4" % "damp-term-63384673")
print("direct GET w3dtmp: ", st, raw[:200])
