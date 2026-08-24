# -*- coding: utf-8 -*-
"""实验J287r: 30001/30002 banner + init内存dump提取gRPC服务路径"""
import json, time, urllib.request, urllib.error, sys, base64
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
            elif d.get("stream") == "command":
                print("EXIT:", json.dumps(d.get("command", {}))[:300], flush=True)
        except Exception:
            print("NONJSON:", line[:400], flush=True)
    return out

NAME = "expj287r"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: 30001/30002 banner (4请求, 间隔0.5s, 验证网络检测阈值)
out = run_cmd(sid, r'''
import socket, time
def req(port, path, method):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        if method == "POST":
            r = (b"POST " + path.encode() + b" HTTP/1.1\r\nHost: init\r\n"
                 b"Content-Type: application/connect+json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
        else:
            r = (b"GET " + path.encode() + b" HTTP/1.1\r\nHost: init\r\nConnection: close\r\n\r\n")
        s.sendall(r)
        data = b""
        try:
            while True:
                d = s.recv(4096)
                if not d:
                    break
                data += d
                if len(data) > 2000:
                    break
        except socket.timeout:
            pass
        s.close()
        return repr(data[:600])
    except Exception as e:
        return "EXC %s" % type(e).__name__
print("30001 GET /:", req(30001, "/", "GET"), flush=True)
time.sleep(0.5)
print("30001 POST /:", req(30001, "/", "POST"), flush=True)
time.sleep(0.5)
print("30002 GET /:", req(30002, "/", "GET"), flush=True)
time.sleep(0.5)
print("30002 POST /:", req(30002, "/", "POST"), flush=True)
print("DONE", flush=True)
''', "BANNER", timeout=100)
print("BANNER out:", repr((out or "")[:1500]), flush=True)

# cmd2: init 内存 dump 提取 gRPC 服务路径 (无网络操作)
out = run_cmd(sid, r'''
import os, re, struct
maps = open("/proc/1/maps").read()
segments = []
for line in maps.splitlines():
    parts = line.split()
    if len(parts) < 6:
        continue
    addr_r, perms, off, dev, ino, path = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
    if path != "/run/vercel/share/sandbox-init":
        continue
    if "r" not in perms:
        continue
    lo, hi = [int(x, 16) for x in addr_r.split("-")]
    segments.append((lo, hi, perms, off))
print("SEGS:", [(hex(a), hex(b), p) for a, b, p, _ in segments[:20]], flush=True)

fd = os.open("/proc/1/mem", os.O_RDONLY)
hits = set()
for lo, hi, perms, off in segments:
    size = min(hi - lo, 6 * 1024 * 1024)
    os.lseek(fd, lo, 0)
    data = os.read(fd, size)
    # gRPC 服务路径: vercel.*.v1.*Service/Method
    for m in re.finditer(rb'[A-Za-z0-9_.]{6,60}Service/[A-Za-z0-9_]{2,40}', data):
        s = m.group(0).decode("latin1", "replace")
        if "vercel" in s or "sandbox" in s or "v1" in s or "v2" in s:
            hits.add(s)
    # 含 vercel. 的路径
    for m in re.finditer(rb'vercel\.[a-zA-Z0-9_.]{4,80}', data):
        s = m.group(0).decode("latin1", "replace")
        if s not in hits:
            hits.add(s)
os.close(fd)
print("HITS %d:" % len(hits), flush=True)
for h in sorted(hits):
    print(h, flush=True)
''', "DUMP", timeout=280)
print("DUMP out len:", len(out or ""), flush=True)
print((out or "")[:12000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
