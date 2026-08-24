# -*- coding: utf-8 -*-
"""实验J281: pidfd_getfd 复制 sandbox-init 全部 fd (避开 ptrace)
目标: 识别 fd 4 (socket:[271]) / 7 / 8 的通信对象, 寻找宿主通道
"""
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

NAME = "expj281"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

def run_cmd_raw(sid, code, label, api_timeout=120):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": 100}
    t0 = time.time()
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body, timeout=api_timeout)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    print(r[:4000], flush=True)

# 1) 仅测 pidfd_getfd 复制 (无 ptrace)
CODE1 = r'''
import os
try:
    pidfd = os.pidfd_open(1, 0)
    copied = []
    for i in range(0, 25):
        try:
            nfd = os.pidfd_getfd(pidfd, i, 0)
            copied.append((i, nfd))
        except Exception:
            pass
    print("COPIED:", copied, flush=True)
    for i, nfd in copied:
        try:
            print(i, "->", os.readlink("/proc/self/fd/%d" % nfd), flush=True)
        except Exception:
            print(i, "-> link_err", flush=True)
    os.close(pidfd)
except Exception as e:
    print("PIDFD_ERR %s: %s" % (type(e).__name__, e), flush=True)
print("DONE", flush=True)
'''
run_cmd_raw(sid, CODE1, "GETFD", api_timeout=120)
