# 实验J186: connect协议探测30001/23456 + 修正HPACK重试30002 + 完整方法列表
# j185: 找到 gRPC 路径 /vercel.sandbox.spawn.v1.SpawnService/{Spawn,Kill,Ping}
# 本步: 1)connect协议: POST Ping/Spawn + JSON/proto 内容类型 -> 30001/23456
#       2)修正HPACK(:path字面量) 重试 30002 gRPC
#       3)提取全部 SpawnService/ 方法
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

NAME = "expj186"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: connect 协议探测 (30001/23456)
PA = r'''
import os, socket
out = open("/tmp/d186a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def http(port, method, path, headers, body=b"", to=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", port))
        hdrs = f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n"
        for k, v in headers.items():
            hdrs += f"{k}: {v}\r\n"
        hdrs += f"Content-Length: {len(body)}\r\n\r\n"
        s.send(hdrs.encode() + body)
        d = b""
        try:
            while True:
                b = s.recv(4096)
                if not b:
                    break
                d += b
                if len(d) > 2500:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
paths = ["/vercel.sandbox.spawn.v1.SpawnService/Ping",
         "/vercel.sandbox.spawn.v1.SpawnService/Spawn",
         "/vercel.sandbox.spawn.v1.SpawnService/Kill"]
for port in [30001, 23456, 30002]:
    for path in paths:
        for ct, body in [("application/json", b"{}"),
                         ("application/json", b""),
                         ("application/proto", b"")]:
            d = http(port, "POST", path,
                     {"Content-Type": ct, "Connect-Protocol-Version": "1"},
                     body)
            p("CALL", port, path, ct, "->", d[:350])
            out.flush()
p("done")
out.close()
'''

# PB: 修正 HPACK 重试 30002
PB = r'''
import os, socket, struct
out = open("/tmp/d186b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def lit(s):
    b = s.encode()
    return bytes([len(b)]) + b
def hpack(name, value):
    # 静态表索引: 1=:authority 2=:method GET 3=:method POST 4=:path / 6=:scheme http
    idx = {"content-type": 31, "te": 50, ":method": 3, ":scheme": 6}
    if name in idx:
        return bytes([0x80 | idx[name]])
    return b"\x00" + lit(name) + lit(value)
def frame(ftype, flags, stream, payload):
    return struct.pack(">I", len(payload))[1:] + bytes([ftype, flags]) + struct.pack(">I", stream) + payload
def grpc_call(path, body=b"", to=4):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", 30002))
        s.send(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
        s.send(frame(4, 0, 0, b""))
        hp = hpack(":method", "POST") + hpack(":scheme", "http") + \
             b"\x00" + lit(":path") + lit(path) + \
             b"\x00" + lit(":authority") + lit("127.0.0.1:30002") + \
             hpack("content-type", "application/grpc") + hpack("te", "trailers")
        s.send(frame(1, 0x1, 1, hp))
        body2 = b"\x00" + struct.pack(">I", len(body)) + body
        s.send(frame(0, 0x1, 1, body2))
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
for path in ["/vercel.sandbox.spawn.v1.SpawnService/Ping",
             "/vercel.sandbox.spawn.v1.SpawnService/Spawn",
             "/vercel.sandbox.spawn.v1.SpawnService/Kill",
             "/grpc.health.v1.Health/Check"]:
    d = grpc_call(path)
    p("H2", path, d[:400])
    out.flush()
p("done")
out.close()
'''

# PC: 全部 SpawnService 方法
PC = r'''
import os, re
out = open("/tmp/d186c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
pat = re.compile(rb"/vercel\.sandbox\.spawn\.v1\.SpawnService/[A-Za-z0-9_]+")
seen = set()
fd = os.open("/run/vercel/share/sandbox-init", os.O_RDONLY)
while True:
    d = os.read(fd, 65536)
    if not d:
        break
    for m in pat.finditer(d):
        s = m.group(0)
        if s not in seen:
            seen.add(s)
            p("M", s.decode())
os.close(fd)
p("n", len(seen))
p("done")
out.close()
'''

steps = [
    ("connect-probe", "/tmp/d186a.txt", PA),
    ("h2c-fixed", "/tmp/d186b.txt", PB),
    ("methods", "/tmp/d186c.txt", PC),
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
