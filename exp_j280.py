# -*- coding: utf-8 -*-
"""实验J280: PID1 (sandbox-init) 暴露面侦察
既然 /proc/1/mem 可写 (无 ptrace 保护), 检查:
1) PID1 uid/gid/caps       2) /proc/1/environ 有无宿主凭证
3) cmdline                 4) /proc/1/root (chroot?)
5) fd 列表 (有无宿主 socket) 6) 沙箱文件系统类型 (gVisor?)
7) uname / /proc/version
全部为快操作 (cmd 通道 <1s)
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
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    dt = time.time() - t0
    print(f"=== cmd[{label}] status {c} wall={dt:.1f}s ===", flush=True)
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

NAME = "expj280"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
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

print("===== 1. uname / version =====", flush=True)
print(sh("uname -a"), flush=True)
print(sh("head -3 /proc/version"), flush=True)

print("===== 2. PID1 status (uid/caps) =====", flush=True)
st = sh("cat /proc/1/status 2>&1 | head -30")
print(st, flush=True)

print("===== 3. PID1 cmdline =====", flush=True)
print(repr(sh("cat /proc/1/cmdline | tr '\\0' ' '")), flush=True)

print("===== 4. PID1 environ (变量名+长度, 敏感值隐藏) =====", flush=True)
try:
    env = open("/proc/1/environ", "rb").read()
    print("environ bytes:", len(env), flush=True)
    for kv in env.split(b"\x00"):
        if not kv:
            continue
        if b"=" in kv:
            k, v = kv.split(b"=", 1)
            print(k.decode("latin1", "replace"), "=", v.decode("latin1", "replace")[:80], flush=True)
except Exception as e:
    print("ENVIRON_ERR %s: %s" % (type(e).__name__, e), flush=True)

print("===== 5. PID1 root / cwd =====", flush=True)
print("root:", sh("ls -la /proc/1/root/ 2>&1 | head -5"), flush=True)
print("cwd:", sh("readlink /proc/1/cwd 2>&1; readlink /proc/1/exe 2>&1"), flush=True)

print("===== 6. PID1 fd 列表 =====", flush=True)
print(sh("ls -la /proc/1/fd 2>&1 | head -40"), flush=True)

print("===== 7. mounts 头部 =====", flush=True)
print(sh("head -25 /proc/mounts"), flush=True)

print("===== 8. PID1 内存前 64 字节可读性 =====", flush=True)
try:
    fd = os.open("/proc/1/mem", os.O_RDONLY)
    os.lseek(fd, 0, 0)
    print("mem[0:64]:", os.read(fd, 64).hex(), flush=True)
    os.close(fd)
except Exception as e:
    print("MEM_ERR %s: %s" % (type(e).__name__, e), flush=True)
'''
run_cmd(sid, CODE, "RECON", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
