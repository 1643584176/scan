# 实验J185: biz.txt 定向grep(spawn服务名/方法) + 30002 h2c gRPC探测
# j184: 发现 spawnconnect.SpawnServiceHandler + h2c HTTP/2! 30002=gRPC端点
# 本步: 1)grep biz.txt: spawn/Service/方法名/vercel内部串
#       2)手写 h2c 帧连 30002 探测 SpawnService 方法
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

def bashfile(sid, cmd, label, n=10000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj185"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: grep biz.txt (轻量逐行过滤, 不读全文件)
PA = r'''
import os
out = open("/tmp/d185a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
KEYS = [b"spawn", b"Service", b"/vercel", b"vercel.sandbox", b"30002", b"30001",
        b"23456", b"grpc", b"h2c", b"command", b"exec", b"pty", b"stream",
        b"health", b"handshake", b"auth", b"sign", b"token", b"secret", b"key"]
seen = set()
n = 0
with open("/tmp/biz.txt", "rb") as fh:
    for ln in fh:
        low = ln.lower()
        if any(k in low for k in KEYS):
            s = ln.strip()
            if s in seen:
                continue
            seen.add(s)
            p("HIT", s[:220])
            n += 1
            if n >= 300:
                p("LIMIT")
                break
p("n", n)
p("done")
out.close()
'''

# PB: gRPC 服务路径模式搜索 (XxxService/Method 或 /vercel...)
PB = r'''
import os, re
out = open("/tmp/d185b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
# 在原始二进制中搜 gRPC 路径模式: /包.服务/方法
pat = re.compile(rb"/[A-Za-z0-9_.\-]{3,60}/[A-Za-z0-9_.\-]{2,60}")
seen = set()
fd = os.open("/run/vercel/share/sandbox-init", os.O_RDONLY)
pos = 0
while pos < 0xA30000 + 0x6dc40:  # text+rodata+data
    os.lseek(fd, pos, 0)
    d = os.read(fd, 65536)
    if not d:
        break
    for m in pat.finditer(d):
        s = m.group(0)
        if s not in seen:
            seen.add(s)
            p("GRPC", s[:120])
            if len(seen) > 200:
                p("LIMIT")
                pos = 1 << 60
                break
    pos += len(d)
os.close(fd)
p("n", len(seen))
p("done")
out.close()
'''

# PC: h2c gRPC 探测 30002 (手写HTTP/2帧)
PC = r'''
import os, socket, struct
out = open("/tmp/d185c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def hpack_encode(name, value):
    # 简化 HPACK: 仅处理不索引字面量 (0x00 前缀) + 字符串长度
    def enc(s):
        b = s.encode()
        if len(b) < 127:
            return bytes([len(b)]) + b
        return bytes([127]) + struct.pack(">H", len(b)) + b
    r = b""
    if name == ":method":
        r += b"\x82"
    elif name == ":scheme":
        r += b"\x86"
    elif name == ":path":
        r += b"\x84"
    elif name == ":authority":
        r += b"\x81"
    elif name == "content-type":
        r += b"\x00" + enc("content-type")
        r += enc(value)
        return r
    elif name == "te":
        r += b"\x00" + enc("te")
        r += enc(value)
        return r
    else:
        r += b"\x00" + enc(name)
    r += enc(value)
    return r

def frame(ftype, flags, stream, payload):
    return struct.pack(">I", len(payload))[1:] + bytes([ftype, flags]) + struct.pack(">I", stream) + payload

def grpc_call(path, body=b"", to=4):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", 30002))
        s.send(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
        s.send(frame(4, 0, 0, b""))  # SETTINGS
        hp = hpack_encode(":method", "POST") + hpack_encode(":scheme", "http") + \
             hpack_encode(":path", path) + hpack_encode(":authority", "127.0.0.1:30002") + \
             hpack_encode("content-type", "application/grpc") + hpack_encode("te", "trailers")
        s.send(frame(1, 0x1, 1, hp))  # HEADERS END_HEADERS
        body2 = b"\x00" + struct.pack(">I", len(body)) + body
        s.send(frame(0, 0x1, 1, body2))  # DATA END_STREAM
        d = b""
        try:
            while True:
                b = s.recv(4096)
                if not b:
                    break
                d += b
                if len(d) > 3000:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
# 先试常见 spawn 方法
for path in ["/spawnconnect.SpawnService/Spawn", "/spawnconnect.SpawnService/Exec",
             "/spawnconnect.SpawnService/Ping", "/spawnconnect.SpawnService/Start",
             "/spawn.SpawnService/Spawn", "/vercel.sandbox.SpawnService/Spawn",
             "/SpawnService/Spawn", "/vercel.sandbox.spawn.v1.SpawnService/Spawn",
             "/grpc.health.v1.Health/Check"]:
    d = grpc_call(path)
    p("CALL", path, d[:400])
    out.flush()
p("done")
out.close()
'''

steps = [
    ("grep-biz", "/tmp/d185a.txt", PA),
    ("grpc-paths", "/tmp/d185b.txt", PB),
    ("h2c", "/tmp/d185c.txt", PC),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    bashfile(sid, f"cat {marker}", f"marker[{label}]", 10000)
    if st == "DEAD":
        print(f"\n!!! DEATH after cmd[{label}]", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
