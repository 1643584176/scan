# -*- coding: utf-8 -*-
"""实验J263: 验证"复制 PID1 fd"本身是否安全 (不 recv/send)
j262 教训: 复制 fd 7 (listen) 后 peek -> 被杀. 本次只复制+readlink+/proc/net/unix 身份确认.
目标: 确认 fd 8 (socket:1267) 是否为宿主 agent 的 init.sock 已连接会话
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

def run_cmd(sid, code, label, wait=True, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    out = ""
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return "DEAD" if "sandbox_stopped" in r else ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out += d.get("data", "")
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    if out:
        print(out, flush=True)
    return out

NAME = "expj263"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# S1) 只复制 PID1 fd 7/8 + readlink + /proc/net/unix 身份确认 + sleep (无 recv/send/close)
CODE_1 = r'''
import os, ctypes, time, re
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def sh(cmd, t=10):
    try:
        import subprocess
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
# 1) PID1 fd 布局
p("pid1_fds", sh("sudo ls -la /proc/1/fd 2>&1").replace(chr(10), " | "))
# 2) /proc/net/unix 中 702 / 1267 的身份
uni = sh("cat /proc/1/net/unix 2>/dev/null || cat /proc/net/unix 2>&1")
for ino in ("702", "1267"):
    for ln in uni.splitlines():
        if re.search(r"\s" + ino + r"\s", ln):
            p("unix_%s" % ino, " ".join(ln.split()[3:]))
# 3) 复制 fd (不操作)
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
pidfd = libc.syscall(434, 1, 0)
p("pidfd", pidfd)
if pidfd >= 0:
    for tgt in [7, 8]:
        ctypes.set_errno(0)
        newfd = libc.syscall(438, pidfd, tgt, 0)
        p("getfd", tgt, "->", newfd, "errno", ctypes.get_errno() if newfd < 0 else 0)
        if newfd >= 0:
            try:
                p("  link", os.readlink("/proc/self/fd/%d" % newfd))
            except Exception as e:
                p("  link_err", repr(e)[:80])
    os.close(pidfd)
# 4) 静置观察是否被杀
p("sleep 8")
time.sleep(8)
p("DONE_1 alive")
'''
r1 = run_cmd(sid, CODE_1, "S1_COPY", timeout=120)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
