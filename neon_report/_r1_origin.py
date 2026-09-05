# -*- coding: utf-8 -*-
"""Recon: damp-term origin + transfer_status residue on A + project metadata."""
import json
import time
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}

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


# 1. project details: both projects
for pid in ("orange-sun-90493739", "damp-term-63384673"):
    st, out = call("GET", "/projects/%s" % pid)
    print("== project %s -> %s" % (pid, st))
    if st == 200:
        p = json.loads(out).get("project", {})
        for k in ("id", "name", "org_id", "created_at", "updated_at", "creation_source",
                  "transfer_status", "branch_logical_size_limit", "region_id",
                  "owner_id", "store_passwords", "settings"):
            if k in p:
                v = p[k]
                print("   %s = %s" % (k, json.dumps(v)[:300]))
    else:
        print("   raw:", out[:300])

# 2. A project auth integration status (transfer residue?)
st, out = call("GET", "/projects/orange-sun-90493739/auth/integrations")
print("== legacy auth integrations A ->", st)
print("   ", out[:600])

# 3. org audit: api keys on org (who/what created)
st, out = call("GET", "/organizations/org-flat-dawn-91601224/api_keys")
print("== org api_keys ->", st)
print("   ", out[:800])

# 4. projects/shared again + full /projects list fields
st, out = call("GET", "/projects?org_id=org-flat-dawn-91601224")
print("== projects full ->", st)
if st == 200:
    for p in json.loads(out).get("projects", []):
        print("   ", p.get("id"), "|", p.get("name"), "| created:", p.get("created_at"),
              "| source:", p.get("creation_source"), "| owner:", p.get("owner_id"))
