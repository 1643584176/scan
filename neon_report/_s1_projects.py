# -*- coding: utf-8 -*-
"""Neon staging: list projects under org + snapshots + branches (read-only)"""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
ORG = "org-flat-dawn-91601224"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)


def call(method, path, body=None, token=None):
    headers = dict(HB)
    if token:
        headers["Authorization"] = "Bearer " + token
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body)
    conn.request(method, API_BASE + path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    return resp.status, data[:6000]


st, out = call("GET", "/projects?org_id=" + ORG, token=APIKEY)
print("== GET /projects?org_id= ->", st)
projs = []
if st == 200:
    for p in json.loads(out).get("projects", []):
        projs.append(p)
        print("   project:", p.get("id"), "|", p.get("name"), "| org:", p.get("org_id"),
              "| settings:", p.get("settings", {}).get("enable_anonymization", "?"))
else:
    print("   raw:", out[:400])

if not projs:
    raise SystemExit("no projects")

for p in projs[:3]:
    pid = p["id"]
    st, out = call("GET", "/projects/%s/snapshots" % pid, token=APIKEY)
    print("== snapshots of %s -> %s" % (pid, st))
    if st == 200:
        snaps = json.loads(out).get("snapshots", [])
        print("   count:", len(snaps))
        for s in snaps[:8]:
            print("   ", s.get("id"), "branch:", s.get("branch_id"), s.get("status"),
                  "| created:", s.get("created_at"), "| type:", s.get("snapshot_type", "?"),
                  "| via:", s.get("created_via", "?"))
    else:
        print("   raw:", out[:400])
    st, out = call("GET", "/projects/%s/branches" % pid, token=APIKEY)
    print("== branches of %s -> %s" % (pid, st))
    if st == 200:
        for b in json.loads(out).get("branches", []):
            print("   branch:", b.get("id"), "|", b.get("name"), "| primary:", b.get("primary"),
                  "| state:", b.get("state", "?"))
    else:
        print("   raw:", out[:400])
