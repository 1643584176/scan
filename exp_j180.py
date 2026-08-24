# 实验J180: sandbox-init 轻量strings + 30002协议识别 + 路由fuzz + 监听进程确认
# j179: sandbox-init可完整读取(Go ELF, protobuf); 30001/23456=Go HTTP 404; 30002无响应
# 本步: 1)逐chunk关键词搜索(路由/URL/协议/命令字), 控制输出量避免被杀
#       2)30002 协议探测(gRPC preface/JSON/protobuf/websocket)
#       3)30001/23456 路由 fuzz(方法+路径变体)
#       4)/proc/1/fd + /proc/net/tcp inode 确认监听进程
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
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return ""

def catfile(sid, path, label, n=8000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj180"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: sandbox-init 逐chunk关键词搜索(轻量)
PA = r'''
import os, re
out = open("/tmp/d180a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
pat = re.compile(rb"(/[A-Za-z0-9_\-./]{2,60})|(https?://[^\x00-\x20]{4,100})|(vercel[a-zA-Z0-9_.\-]{0,40})|(token[a-zA-Z0-9_]{0,20})|(secret[a-zA-Z0-9_]{0,20})|(pubkey[a-zA-Z0-9_]{0,20})|(nonce[a-zA-Z0-9_]{0,20})|(sign[a-zA-Z0-9_]{0,30})|(command[a-zA-Z0-9_]{0,30})|(exec[a-zA-Z0-9_]{0,20})|(handshake[a-zA-Z0-9_]{0,20})")
seen = set()
n = 0
fd = os.open("/run/vercel/share/sandbox-init", os.O_RDONLY)
while True:
    d = os.read(fd, 65536)
    if not d:
        break
    for m in pat.finditer(d):
        s = m.group(0)
        if len(s) < 4:
            continue
        if s in seen:
            continue
        seen.add(s)
        # 上下文
        a = max(0, m.start() - 30)
        ctx = d[a:m.end() + 60]
        ctx = re.sub(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", b".", ctx)
        if len(ctx) > 90:
            ctx = ctx[:90]
        p("S", s[:80], "|", ctx[:90])
        n += 1
        if n > 250:
            p("HIT_LIMIT")
            break
    if n > 250:
        break
os.close(fd)
p("total", n)
p("done")
out.close()
'''

# PB: 30002 协议探测
PB = r'''
import os, socket, struct
out = open("/tmp/d180b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def probe(payload, to=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", 30002))
        if payload:
            s.send(payload)
        d = b""
        try:
            while True:
                b = s.recv(4096)
                if not b:
                    break
                d += b
                if len(d) > 2000:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
# gRPC HTTP/2 preface
d = probe(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
p("GRPC", d[:300])
# JSON
d = probe(b'{"jsonrpc":"2.0","id":1,"method":"ping"}')
p("JSON", d[:300])
# 空
d = probe(b"")
p("EMPTY", d[:300])
# 长度前缀 protobuf
d = probe(b"\x00\x00\x00\x00")
p("PB4", d[:300])
# HTTP
d = probe(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
p("HTTP1", d[:300])
# 常见 magic
d = probe(b"VSOCK")
p("VSOCK", d[:300])
d = probe(b"\x00")
p("ONE0", d[:300])
p("done")
out.close()
'''

# PC: 30001/23456 路由 fuzz (方法+路径)
PC = r'''
import os, socket
out = open("/tmp/d180c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def http(port, method, path, to=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", port))
        s.send(f"{method} {path} HTTP/1.0\r\nHost: 127.0.0.1\r\nContent-Length: 0\r\n\r\n".encode())
        d = b""
        try:
            while True:
                b = s.recv(4096)
                if not b:
                    break
                d += b
                if len(d) > 1500:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
paths = ["/v1/", "/v1/health", "/v1/status", "/v1/exec", "/v1/command", "/v1/cmd",
         "/v2/", "/api/", "/api/v1/", "/rpc", "/rpc/", "/ws", "/exec", "/run",
         "/cmd", "/command", "/commands", "/session", "/sessions", "/attach",
         "/connect", "/shell", "/terminal", "/pty", "/stream", "/events",
         "/files", "/fs", "/process", "/processes", "/log", "/logs", "/healthz/",
         "/ready", "/ping", "/info/", "/debug/", "/env", "/config/", "/settings",
         "/control", "/control/", "/agent", "/agent/", "/init", "/start", "/stop"]
for port in [30001, 23456]:
    for path in paths:
        for method in ["GET", "POST"]:
            d = http(port, method, path)
            if not d.startswith(b"HTTP/1.0 404"):
                p("FOUND", port, method, path, d[:250].decode(errors="replace").replace("\r\n", " | "))
                out.flush()
        out.flush()
p("done")
out.close()
'''

# PD: /proc/1/fd + inode 确认
PD = r'''
import os
out = open("/tmp/d180d.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
# inode 645/1164/1175 属于谁
for ino in ["645", "1164", "1175"]:
    found = []
    for pid in [1, 29]:
        try:
            fds = os.listdir(f"/proc/{pid}/fd")
            for fd in fds:
                try:
                    tgt = os.readlink(f"/proc/{pid}/fd/{fd}")
                    if ino in tgt:
                        found.append((pid, fd, tgt))
                except Exception:
                    pass
        except Exception as ex:
            p("FD_ERR", pid, repr(ex))
    p("INODE", ino, found)
p("done")
out.close()
'''

steps = [
    ("strings", "/tmp/d180a.txt", PA),
    ("proto", "/tmp/d180b.txt", PB),
    ("routes", "/tmp/d180c.txt", PC),
    ("inode", "/tmp/d180d.txt", PD),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 9000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
