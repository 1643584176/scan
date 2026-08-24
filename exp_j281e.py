# -*- coding: utf-8 -*-
"""调试快照列表 API 变体"""
import json, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=60):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

paths = [
    f"/v2/sandboxes/snapshots?teamId={TEAM}&limit=50",
    f"/v2/sandboxes/snapshots?teamId={TEAM}&projectId={PROJ}&limit=50",
    f"/v2/sandboxes/snapshots?teamId={TEAM}&project={PROJ}&limit=50",
    f"/v2/sandboxes?teamId={TEAM}&includeSnapshots=true&limit=50",
]
for path in paths:
    c, r = api("GET", path)
    print(path.split("?")[1][:70], "->", c, r[:300], flush=True)
