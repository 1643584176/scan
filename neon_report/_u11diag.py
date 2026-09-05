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
for b in json.loads(d).get("branches", []):
    print("  %-30s %s state=%s" % (b.get("name"), b.get("id"), b.get("state")))

SRC = None
for b in json.loads(d).get("branches", []):
    if b.get("name") == "u11-src":
        SRC = b["id"]
print("SRC:", SRC)

if SRC:
    for path in [
        "/projects/%s/branches/%s/connection_uri?database_name=neondb&role_name=neondb_owner" % (PA, SRC),
        "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (PA, SRC),
    ]:
        st, d = call("GET", path)
        print("path:", path)
        print("  ->", st, d[:300])
        time.sleep(1)
