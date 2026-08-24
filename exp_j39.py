# 实验J39: init.sock HTTP/gRPC 协议深度探测
# 目标: 枚举 HTTP 端点, gRPC 反射, 提取 service/method 路径, pubkey 分析
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

NAME = "expj39"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, base64, re, os

S = "/run/vercel/share/init.sock"

def http_req(path, method="GET", headers=None, body=None, raw=False):
    """发送 HTTP/1.1 请求到 init.sock"""
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(S)
    if raw:
        req = path
    else:
        req = "%s %s HTTP/1.1\r\nHost: localhost\r\n" % (method, path)
        if headers:
            for k, v in headers.items():
                req += "%s: %s\r\n" % (k, v)
        if body is not None:
            req += "Content-Length: %d\r\n" % len(body)
        req += "\r\n"
        if body is not None:
            req += body
    s.sendall(req.encode() if isinstance(req, str) else req)
    data = b""
    try:
        while True:
            chunk = s.recv(8192)
            if not chunk:
                break
            data += chunk
            if len(data) > 60000:
                break
    except socket.timeout:
        pass
    s.close()
    return data

print("===== [1] pubkey 分析 =====", flush=True)
pk = "nwfpfMhbLSv98yT0LZmrqZcRIXAVaQ6vwyUwhhKJChs="
raw = base64.b64decode(pk)
print("b64 len=%d decoded=%d bytes -> %r" % (len(pk), len(raw), raw.hex()), flush=True)
import subprocess
print(subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout, flush=True)

print("===== [2] 基础 HTTP 探测 =====", flush=True)
for path in ["/", "/health", "/healthz", "/version", "/v1", "/api", "/grpc", "/debug",
             "/metrics", "/status", "/info", "/ping", "/ready"]:
    d = http_req(path)
    first = d.split(b"\r\n", 1)[0]
    print("%-12s -> %s (len=%d)" % (path, first.decode(errors='replace'), len(d)), flush=True)

print("===== [3] 方法探测 (OPTIONS/POST/PUT/DELETE) =====", flush=True)
for m in ["OPTIONS", "POST", "PUT", "DELETE", "HEAD"]:
    d = http_req("/", method=m)
    print("%-8s -> %r" % (m, d[:150]), flush=True)

print("===== [4] POST / HTTP 响应体 =====", flush=True)
d = http_req("/", method="POST", body="{}")
print(d[:500], flush=True)

print("===== [5] gRPC 探测 =====", flush=True)
# gRPC reflection 请求 (http/1.1 + content-type application/grpc)
grpc_reflect = (
    b"\x00\x00\x00\x00\x00"  # 5-byte length prefix (0)
)
# 尝试常见 gRPC 路径
for path in ["/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo",
             "/grpc.reflection.v1.ServerReflection/ServerReflectionInfo",
             "/grpc.health.v1.Health/Check",
             "/grpc.health.v1.Health/Watch"]:
    d = http_req(path, method="POST",
                 headers={"Content-Type": "application/grpc", "TE": "trailers"},
                 body=grpc_reflect)
    print("%-70s -> %r" % (path, d[:200]), flush=True)

print("===== [6] 二进制 gRPC 路径提取 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
# gRPC 方法路径: /package.Service/Method
paths = re.findall(rb"/[a-zA-Z0-9_.]{3,60}/[a-zA-Z0-9_]{3,60}", b)
uniq = sorted(set(p.decode('latin1') for p in paths))
print("total path-like:", len(uniq), flush=True)
for p in uniq[:60]:
    print("  %s" % p, flush=True)

print("===== [7] 更多协议字符串 =====", flush=True)
pats = [rb"HTTP/1\.[01]", rb"h2c", rb"grpc[^a-zA-Z]?", rb"Content-Type", rb"authorization",
        rb"Bearer", rb"signature", rb"nonce", rb"timestamp", rb"ed25519", rb"hmac",
        rb"pubkey", rb"private", rb"unauthen", rb"forbidden", rb"permission"]
for pat in pats:
    ms = re.findall(rb"[\x20-\x7e]{0,80}" + pat + rb"[\x20-\x7e]{0,80}", b)
    print("PAT %r: %d hits" % (pat, len(ms)), flush=True)
    for m in ms[:6]:
        print("    %r" % m.decode('latin1'), flush=True)

print("===== [8] 文件服务特征字符串 =====", flush=True)
for kw in [b"fileID", b"byKey", b"ReadAt", b"Pwrite", b"open", b"create", b"delete", b"list"]:
    ms = re.findall(rb"[\x20-\x7e]{0,60}" + kw + rb"[\x20-\x7e]{0,60}", b)
    print("KW %r: %d" % (kw, len(ms)), flush=True)
    for m in ms[:8]:
        print("    %r" % m.decode('latin1'), flush=True)
'''
run_cmd(sid, SCAN, "init-sock-http-probe", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
