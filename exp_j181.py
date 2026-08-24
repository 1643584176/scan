# 实验J181: 严格strings提取 + 神秘路径测试 + 30002 TLS探测
# j180: 命中神秘常量 /jU8rfXxa6EoYX1hiUl4M/...(46ch base64url 疑似API路径); 30002全探测无响应
# 本步: 1)严格提取 16+ 连续可打印串, 过滤代码误报, 全量输出(分批)
#       2)神秘路径测 30001/23456 (GET/POST + Host变体)
#       3)30002 TLS ClientHello + websocket + 长度前缀变体
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

def catfile(sid, path, label, n=10000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj181"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: 严格 strings - 16+ 连续可打印, 过滤明显代码, 输出全量到文件(分段输出)
PA = r'''
import os, re
out = open("/tmp/d181a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
d = open("/run/vercel/share/sandbox-init", "rb").read()
p("size", len(d))
strs = re.findall(rb"[\x20-\x7e]{16,}", d)
p("nstrs", len(strs))
# 高价值: 含 / 或 . 或 _ 或 - 的长串; 排除常见代码串
skip = re.compile(rb"^[A-Za-z0-9_./]{16,}$")  # 仅保留这些字符 -> 看起来像路径/域名/标识
n = 0
for s in strs:
    # 过滤汇编误报: 含不可见序列的已排除(只取纯可打印)
    if len(s) < 24 and not re.search(rb"[/._-]", s):
        continue
    if s.startswith(b"___") or s.startswith(b".text") or s.startswith(b".data"):
        continue
    p("S", s[:160])
    n += 1
    if n >= 400:
        p("LIMIT", n)
        break
p("total", n)
p("done")
out.close()
'''

# PB: 神秘路径测试
PB = r'''
import os, socket
out = open("/tmp/d181b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def http(port, method, path, headers=None, body=b"", to=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", port))
        hdrs = f"{method} {path} HTTP/1.0\r\nHost: 127.0.0.1\r\n"
        if headers:
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
                if len(d) > 1500:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
PATH = "/jU8rfXxa6EoYX1hiUl4M/3Wubc93_THmJZDHRl-jE/Vx_3uhJ34OD1myaD7X"
for port in [30001, 23456]:
    for method in ["GET", "POST"]:
        d = http(port, method, PATH)
        p("MYST", port, method, d[:300].decode(errors="replace").replace("\r\n", " | "))
        out.flush()
    # Host 变体
    d = http(port, "GET", PATH, headers={"Host": "vercel.com"})
    p("MYST_HOST", port, d[:300].decode(errors="replace").replace("\r\n", " | "))
    d = http(port, "GET", PATH, headers={"X-Vercel-Sandbox-Token": "x"})
    p("MYST_HDR", port, d[:300].decode(errors="replace").replace("\r\n", " | "))
    # 无路径(仅 Host)
    d = http(port, "GET", "/", headers={"Host": "vercel.com"})
    p("HOST_ONLY", port, d[:200].decode(errors="replace").replace("\r\n", " | "))
    # OPTIONS
    d = http(port, "OPTIONS", "/")
    p("OPTIONS", port, d[:300].decode(errors="replace").replace("\r\n", " | "))
    out.flush()
p("done")
out.close()
'''

# PC: 30002 TLS/WS/变体探测
PC = r'''
import os, socket, struct
out = open("/tmp/d181c.txt", "w")
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
# TLS ClientHello (最小)
tls = bytes.fromhex("16030100c5010000c103033bf3a9f3a9f3a9f3a9f3a9f3a9f3a9f3a9f3a9f3a9f3a9f3a9f3a900002c130113021303c02bc02fc02cc030cca9cca8cc14cc13c009c013c00ac0140039003800880087000a0005000401000000490000000e000c0000096c6f63616c686f7374000a00080006001700180019000b00020100000d001200100401020105010301040102010304010303")
d = probe(tls)
p("TLS", d[:300])
# WS 握手
d = probe(b"GET / HTTP/1.1\r\nHost: 127.0.0.1:30002\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n")
p("WS", d[:300])
# UDP 探测
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    s.sendto(b"hello", ("127.0.0.1", 30002))
    try:
        d, _ = s.recvfrom(2048)
        p("UDP_RECV", d[:300])
    except socket.timeout:
        p("UDP_TIMEOUT")
    except Exception as ex:
        p("UDP_EXC", repr(ex))
except Exception as ex:
    p("UDP_ERR", repr(ex))
# 长度前缀变体
for lp in [b"\x00\x00\x00\x01", b"\x00\x00\x00\x05", b"\x00\x00\x00\x10", b"\x01\x00\x00\x00"]:
    d = probe(lp + b"ping")
    p("LP", lp.hex(), d[:200])
p("done")
out.close()
'''

steps = [
    ("strs", "/tmp/d181a.txt", PA),
    ("myst", "/tmp/d181b.txt", PB),
    ("tls", "/tmp/d181c.txt", PC),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 10000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
