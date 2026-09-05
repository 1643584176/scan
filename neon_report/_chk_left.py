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
resp = conn.getresponse()
data = json.loads(resp.read().decode("utf-8", "replace"))
conn.close()
print("status:", resp.status)
for b in data.get("branches", []):
    print("%-32s %-28s parent=%s ra=%s state=%s" % (
        b.get("name"), b.get("id"), b.get("parent_id"),
        b.get("restricted_actions"), b.get("current_state")))
