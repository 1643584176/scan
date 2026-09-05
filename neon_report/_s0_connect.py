# -*- coding: utf-8 -*-
"""Neon staging connectivity check: bearer api key, list projects & snapshots (read-only)"""
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


def call(method, path, body=None, token=None, extra=None):
    headers = dict(HB)
    if token:
        headers["Authorization"] = "Bearer " + token
    if extra:
        headers.update(extra)
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body)
    conn.request(method, API_BASE + path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    return resp.status, data[:4000]


# 1. whoami with api key
st, out = call("GET", "/users/me", token=APIKEY)
print("== GET /users/me ->", st)
if st == 200:
    me = json.loads(out)
    print("   user:", me.get("email"), "| id:", me.get("id"))
else:
    print("   raw:", out[:200])
    raise SystemExit("api key rejected; need fresh staging creds")

# 2. list projects (look for second project for cross-project control)
st, out = call("GET", "/projects", token=APIKEY)
print("== GET /projects ->", st)
projs = []
if st == 200:
    for p in json.loads(out).get("projects", []):
        projs.append((p.get("id"), p.get("name"), p.get("org_id"), p.get("branch_logical_size_limit")))
        print("   project:", p.get("id"), p.get("name"), "org=", p.get("org_id"))
else:
    print("   raw:", out[:300])

# 3. snapshots on first project (read-only baseline)
if projs:
    pid = projs[0][0]
    st, out = call("GET", "/projects/%s/snapshots" % pid, token=APIKEY)
    print("== GET /projects/%s/snapshots -> %s" % (pid, st))
    if st == 200:
        snaps = json.loads(out).get("snapshots", [])
        print("   count:", len(snaps))
        for s in snaps[:10]:
            print("   ", s.get("id"), s.get("branch_id"), s.get("status"), s.get("created_at"))
    else:
        print("   raw:", out[:300])
    # branches list
    st, out = call("GET", "/projects/%s/branches" % pid, token=APIKEY)
    print("== GET /projects/%s/branches -> %s" % (pid, st))
    if st == 200:
        for b in json.loads(out).get("branches", []):
            print("   branch:", b.get("id"), b.get("name"), b.get("primary"))
    else:
        print("   raw:", out[:300])
