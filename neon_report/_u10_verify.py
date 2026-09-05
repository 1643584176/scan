# -*- coding: utf-8 -*-
import json, ssl, http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
conn.request("GET", API_BASE + "/projects/%s/branches" % PA,
             headers=dict(HB, Authorization="Bearer " + APIKEY))
r = conn.getresponse()
d = json.loads(r.read().decode("utf-8", "replace"))
conn.close()
print("branches:", r.status)
for b in d.get("branches", []):
    print("  %-40s %-30s primary=%s default=%s ra=%s" % (
        b.get("name"), b.get("id"), b.get("primary"), b.get("default"),
        b.get("restricted_actions")))
conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
conn.request("GET", API_BASE + "/projects/%s/endpoints" % PA,
             headers=dict(HB, Authorization="Bearer " + APIKEY))
r = conn.getresponse()
d2 = json.loads(r.read().decode("utf-8", "replace"))
conn.close()
print("endpoints:", r.status)
for e in d2.get("endpoints", []):
    print("  %s %s %s" % (e.get("id"), e.get("branch_id"), e.get("type")))
