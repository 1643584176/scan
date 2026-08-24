# 实验J45: Capabilities 确认 + 抓包可行性 + 签名头名挖掘
# 目标: CapEff 位, raw socket 可用性, 协议头名, gRPC 包名候选
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj45"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, os, subprocess

print("===== [1] capabilities =====", flush=True)
print(open("/proc/self/status").read(), flush=True)

print("===== [2] raw socket 测试 =====", flush=True)
try:
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3))
    print("AF_PACKET RAW: OK", flush=True)
    s.close()
except Exception as e:
    print("AF_PACKET RAW FAIL: %s" % e, flush=True)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
    print("AF_INET RAW: OK", flush=True)
    s.close()
except Exception as e:
    print("AF_INET RAW FAIL: %s" % e, flush=True)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    print("IP_HDRINCL: OK", flush=True)
    s.close()
except Exception as e:
    print("IP_HDRINCL FAIL: %s" % e, flush=True)

print("===== [3] 接口与抓包面 =====", flush=True)
for f in ["/sys/class/net", "/proc/net/dev"]:
    print("---", f, "---", flush=True)
    print(open(f).read()[:1500], flush=True)

print("===== [4] 二进制签名头名与路径挖掘 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
# 头名: signature/timestamp 上下文
for kw in [b"signature", b"timestamp"]:
    for m in re.finditer(kw, b):
        s, e = max(0, m.start()-80), min(len(b), m.end()+80)
        ctx = b[s:e]
        if all(32 <= c < 127 or c in (10, 13, 9) for c in ctx):
            print("KW %r @%d: %r" % (kw, m.start(), ctx.decode('latin1')), flush=True)
# HTTP 头名候选 (小写短词, 可能是头)
for m in re.finditer(rb'(?i)["\s\:]([a-z][a-z0-9-]{2,24})["\s\:]', b):
    v = m.group(1)
    if v in (b"signature", b"timestamp", b"authorization", b"x-vercel-signature"):
        print("HEADER CAND: %r @%d" % (v, m.start()), flush=True)

print("===== [5] proto 包名候选 =====", flush=True)
# proto 包名: 小写.小写.v1 或 大写驼峰
pkg_cands = set()
for m in re.finditer(rb"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){1,3}\.v[0-9]+", b):
    pkg_cands.add(m.group(0).decode('latin1'))
for m in re.finditer(rb"[A-Z][a-zA-Z0-9]{3,30}Service", b):
    pkg_cands.add(m.group(0).decode('latin1'))
for p in sorted(pkg_cands)[:80]:
    print("PKG: %r" % p, flush=True)

print("===== [6] gRPC 方法路径模式 =====", flush=True)
# /pkg.Service/Method 完整路径
paths = set()
for m in re.finditer(rb"/[a-z][a-z0-9_.]{2,60}\.[A-Z][A-Za-z0-9]{2,40}/[A-Z][A-Za-z0-9]{2,40}", b):
    paths.add(m.group(0).decode('latin1'))
for p in sorted(paths)[:60]:
    print("GRPC PATH: %r" % p, flush=True)
print("grpc paths total:", len(paths), flush=True)

print("===== [7] 非 gRPC 路径 (自定义 mux) =====", flush=True)
# 短路径: /xxx/yyy 或 /v1/xxx
for m in re.finditer(rb"/v[0-9]+/[a-zA-Z0-9_/-]{2,40}", b):
    print("V: %r" % m.group(0).decode('latin1'), flush=True)
'''
run_cmd(sid, SCAN, "caps-raw-socket-proto-mine", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
