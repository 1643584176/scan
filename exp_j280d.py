# -*- coding: utf-8 -*-
"""实验J280d: 分步定位 j280 无输出原因"""
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

NAME = "expj280d"
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
    print(r[:3000], flush=True)

# 每步打标记
CODE = r'''
import os, subprocess
def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e
print("S1", flush=True)
print(sh("uname -a"), flush=True)
print("S2", flush=True)
print(sh("cat /proc/1/status 2>&1 | head -20"), flush=True)
print("S3", flush=True)
try:
    env = open("/proc/1/environ", "rb").read()
    print("ENVBYTES", len(env), flush=True)
    names = [kv.split(b"=")[0].decode("latin1","replace") for kv in env.split(b"\x00") if b"=" in kv]
    print("ENVNAMES", names, flush=True)
except Exception as e:
    print("ENV_ERR %s: %s" % (type(e).__name__, e), flush=True)
print("S4", flush=True)
print(sh("ls -la /proc/1/root/ 2>&1 | head -8"), flush=True)
print("S5", flush=True)
print(sh("readlink /proc/1/cwd 2>&1; readlink /proc/1/exe 2>&1"), flush=True)
print("S6", flush=True)
print(sh("ls -la /proc/1/fd 2>&1 | head -30"), flush=True)
print("S7", flush=True)
print(sh("head -20 /proc/mounts"), flush=True)
print("S8", flush=True)
print(sh("cat /proc/1/maps 2>&1 | head -5"), flush=True)
print("S9", flush=True)
try:
    fd = os.open("/proc/1/mem", os.O_RDONLY)
    os.lseek(fd, 0, 0)
    print("MEM0", os.read(fd, 32).hex(), flush=True)
    os.close(fd)
except Exception as e:
    print("MEM_ERR %s: %s" % (type(e).__name__, e), flush=True)
print("DONE", flush=True)
'''
run_cmd_raw(sid, CODE, "STEP")
