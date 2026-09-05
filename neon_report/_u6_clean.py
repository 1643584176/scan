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


st, d = call("GET", "/projects/%s/branches" % PA)
print("branches:", st)
try:
    for b in json.loads(d).get("branches", []):
        if b.get("name", "").startswith("u6-"):
            print("  delete", b["name"], b["id"])
            s2, d2 = call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
            print("    ->", s2, d2[:120])
except Exception as e:
    print("err", e, d[:300])
