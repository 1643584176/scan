# -*- coding: utf-8 -*-
"""实验J280e: S6-S9 部分 (fd/mounts/maps/mem)"""
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

NAME = "expj280e"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

def run_cmd_raw(sid, code, label):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": 100}
    t0 = time.time()
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    print(r[:5000], flush=True)

CODE = r'''
import os, subprocess
def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e
print("===== fd =====", flush=True)
print(sh("ls -la /proc/1/fd 2>&1"), flush=True)
print("===== mounts =====", flush=True)
print(sh("cat /proc/mounts | head -30"), flush=True)
print("===== maps head =====", flush=True)
print(sh("cat /proc/1/maps | head -8"), flush=True)
print("===== mem[0:32] =====", flush=True)
try:
    fd = os.open("/proc/1/mem", os.O_RDONLY)
    os.lseek(fd, 0, 0)
    print("MEM0", os.read(fd, 32).hex(), flush=True)
    os.close(fd)
except Exception as e:
    print("MEM_ERR %s: %s" % (type(e).__name__, e), flush=True)
print("===== capabilities =====", flush=True)
print(sh("grep Cap /proc/1/status"), flush=True)
print(sh("grep Cap /proc/self/status"), flush=True)
print("===== ns 对比 =====", flush=True)
print("pid1:", sh("readlink /proc/1/ns/mnt /proc/1/ns/pid /proc/1/ns/net 2>&1"), flush=True)
print("self:", sh("readlink /proc/self/ns/mnt /proc/self/ns/pid /proc/self/ns/net 2>&1"), flush=True)
print("===== 网络接口 =====", flush=True)
print(sh("cat /proc/net/dev 2>&1 | head -12"), flush=True)
print("===== 路由 =====", flush=True)
print(sh("cat /proc/net/route 2>&1"), flush=True)
print("DONE", flush=True)
'''
run_cmd_raw(sid, CODE, "S6-S9")
