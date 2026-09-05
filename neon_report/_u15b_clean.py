# -*- coding: utf-8 -*-
import json, ssl, http.client, time

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"

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


for attempt in range(6):
    st, d = call("GET", "/projects/%s/branches" % PA)
    left = [b for b in json.loads(d).get("branches", [])
            if b.get("name", "").startswith(("u11-", "u12-", "u15-"))]
    if not left:
        print("ALL CLEAN on attempt", attempt)
        break
    for b in left:
        st3, d3 = call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
        print("del %s (%s): %s %s" % (b["name"], b["id"], st3, d3[:180]))
    time.sleep(10)

st, d = call("GET", "/projects/%s/branches" % PA)
print("FINAL:")
for b in json.loads(d).get("branches", []):
    print("  %-30s %s" % (b.get("name"), b.get("id")))
