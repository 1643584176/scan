# -*- coding: utf-8 -*-
"""W5k: cleanup - delete X1 permission grant; confirm DELETE semantics."""
import json, ssl, http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()

def api(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    hdr = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY}
    if body is not None:
        hdr["Content-Type"] = "application/json"
        body = json.dumps(body)
    conn.request(method, API_BASE + path, body=body, headers=hdr)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, data

# list current grants
st, d = api("GET", "/projects/%s/permissions" % PA)
print("list:", st, d[:400])
grants = json.loads(d).get("project_permissions", [])
# delete grants not owned by self (the X1 test grant)
for g in grants:
    if g.get("granted_to_email") != "libobo1229@gmail.com":
        st2, d2 = api("DELETE", "/projects/%s/permissions/%s" % (PA, g["id"]))
        print("delete %s -> %d %s" % (g["granted_to_email"], st2, d2[:200]))
st, d = api("GET", "/projects/%s/permissions" % PA)
print("after:", st, d[:300])
