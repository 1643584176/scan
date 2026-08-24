# -*- coding: utf-8 -*-
"""释放快照配额: 列出并删除旧快照"""
import json, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=120):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

# 列出所有沙箱 (找有快照的)
c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&project={PROJ}&limit=50")
print("list sandboxes:", c, flush=True)
try:
    boxes = json.loads(r)
    items = boxes.get("sandboxes", [])
    print("count:", len(items), flush=True)
    for b in items:
        print("-", b.get("name"), b.get("id"), "snapshots:", b.get("snapshotCount"), flush=True)
except Exception as e:
    print("parse err", e, r[:300], flush=True)
    items = []

# 列出快照
c2, r2 = api("GET", f"/v2/sandboxes/snapshots?teamId={TEAM}&projectId={PROJ}&limit=50")
print("\nlist snapshots:", c2, flush=True)
try:
    snaps = json.loads(r2).get("snapshots", [])
    print("snapshot count:", len(snaps), flush=True)
    for s in snaps:
        print("-", s.get("id"), s.get("sourceSessionId"), s.get("sizeBytes"), s.get("createdAt"), flush=True)
except Exception as e:
    print("parse err", e, r2[:300], flush=True)
    snaps = []

# 删除所有快照
for s in snaps:
    c3, r3 = api("DELETE", f"/v2/sandboxes/snapshots/{s['id']}?teamId={TEAM}&projectId={PROJ}")
    print("del", s.get("id"), c3, flush=True)
