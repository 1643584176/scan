# -*- coding: utf-8 -*-
"""删除全部快照释放配额"""
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
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

c, r = api("GET", f"/v2/sandboxes/snapshots?teamId={TEAM}&project={PROJ}&limit=50")
snaps = json.loads(r).get("snapshots", []) if c == 200 else []
print("snapshots:", len(snaps), flush=True)
for s in snaps:
    c3, r3 = api("DELETE", f"/v2/sandboxes/snapshots/{s['id']}?teamId={TEAM}&projectId={PROJ}")
    print("del", s["id"], c3, r3[:120], flush=True)
    if c3 != 200:
        c3b, r3b = api("DELETE", f"/v2/sandboxes/snapshots/{s['id']}?teamId={TEAM}&project={PROJ}")
        print("  retry project=", c3b, r3b[:120], flush=True)

# 顺带删除所有旧实验沙箱 (释放资源)
c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&project={PROJ}&limit=50")
boxes = json.loads(r).get("sandboxes", []) if c == 200 else []
for b in boxes:
    nm = b.get("name")
    if nm and nm.startswith(("exp", "k14", "tupd", "expk", "expi", "expj", "expg", "expf", "expe", "exph")):
        c4, r4 = api("DELETE", f"/v2/sandboxes/{nm}?teamId={TEAM}&projectId={PROJ}")
        print("del sbx", nm, c4, flush=True)
