# -*- coding: utf-8 -*-
"""实验J280c: 完整 RECON 代码原始响应调试"""
import json, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=300):
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

NAME = "expj280c"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE = r'''
import os, subprocess, re
def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e
print("===== 1. uname =====", flush=True)
print(sh("uname -a"), flush=True)
print("===== 2. status =====", flush=True)
print(sh("cat /proc/1/status 2>&1 | head -30"), flush=True)
print("===== 3. cmdline =====", flush=True)
print(repr(sh("cat /proc/1/cmdline | tr '\\0' ' '")), flush=True)
print("===== DONE =====", flush=True)
'''
body = {"command": "python3", "args": ["-c", CODE],
        "wait": True, "logs": True, "timeout": 100}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
print("status:", c, flush=True)
print("RAW:", r[:4000], flush=True)
