# -*- coding: utf-8 -*-
"""Verify PA main branch still exists after cleanup."""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
conn.request("GET", API_BASE + "/projects/orange-sun-90493739/branches",
             headers=dict(HB, Authorization="Bearer " + APIKEY))
resp = conn.getresponse()
out = resp.read().decode("utf-8", "replace")
print("status:", resp.status)
d = json.loads(out)
for b in d.get("branches", []):
    print("   branch:", b.get("id"), b.get("name"), "primary:", b.get("primary"))
print("count:", len(d.get("branches", [])))
