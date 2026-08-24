# 实验J43: curl HTTP/2 + gRPC reflection 枚举
# 目标: 用 curl --http2-prior-knowledge 打通 init.sock/23456/30001, 枚举 gRPC 服务
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

NAME = "expj43"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, os, subprocess

print("===== [1] curl HTTP/2 -> init.sock =====", flush=True)
cmds = [
    ["curl", "-sS", "--http2-prior-knowledge", "--max-time", "8",
     "--unix-socket", "/run/vercel/share/init.sock", "-i", "http://localhost/"],
    ["curl", "-sS", "--http2-prior-knowledge", "--max-time", "8",
     "--unix-socket", "/run/vercel/share/init.sock", "-i", "-X", "POST",
     "-H", "content-type: application/grpc",
     "--data-binary", "@-", "http://localhost/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo"],
]
for c in cmds[:1]:
    r = subprocess.run(c, capture_output=True, text=True, input="", timeout=10)
    print("cmd:", " ".join(c[:6]), flush=True)
    print("RC=%d stdout=%r stderr=%r" % (r.returncode, r.stdout[:800], r.stderr[:400]), flush=True)

print("===== [2] curl HTTP/2 -> 23456/30001 =====", flush=True)
for port in [23456, 30001]:
    for target in ["http://localhost/", "http://[::1]/"]:
        try:
            r = subprocess.run(
                ["curl", "-sS", "--http2-prior-knowledge", "--max-time", "6", "-i", target],
                capture_output=True, text=True, timeout=10)
            print("port %d %s -> RC=%d out=%r err=%r" % (port, target, r.returncode, r.stdout[:400], r.stderr[:200]), flush=True)
        except Exception as e:
            print("port %d %s -> ERR %s" % (port, target, e), flush=True)

print("===== [3] 修正 HPACK gRPC reflection (23456) =====", flush=True)
def h2_grpc(ip, port, path, msg, timeout=5):
    s = socket.socket(socket.AF_INET6 if ":" in ip else socket.AF_INET)
    s.settimeout(timeout)
    s.connect((ip, port))
    s.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n" + b"\x00\x00\x00\x04\x00\x00\x00\x00\x00")
    try:
        s.recv(8192)  # server SETTINGS
    except Exception:
        pass
    def lit_idx(idx, val):
        return bytes([0x40 | idx]) + bytes([len(val)]) + val
    def lit_new(name, val):
        return bytes([0x40]) + bytes([len(name)]) + name + bytes([len(val)]) + val
    hb = b""
    hb += b"\x83"                                       # :method POST
    hb += b"\x86"                                       # :scheme http
    hb += lit_idx(1, path.encode())                    # :path (idx 1 = :path? no - static 1=:authority)
    # 修正: :path 静态表索引是 4 (只指 "/"), 用新名字字面量
    hb = b"\x83\x86" + lit_new(b":path", path.encode()) + lit_idx(2, b"localhost")
    hb += bytes([0x40 | 31]) + bytes([16]) + b"application/grpc"  # content-type (static 31)
    hb += lit_new(b"te", b"trailers")
    hdr = b"\x00\x00" + len(hb).to_bytes(2, "big") + b"\x01\x04\x00\x00\x00\x01" + hb
    body = b"\x00\x00\x00\x00" + bytes([len(msg)]) + msg
    dframe = b"\x00\x00" + len(body).to_bytes(2, "big") + b"\x00\x00\x00\x00\x00\x01" + body
    s.sendall(hdr + dframe)
    resp = b""
    try:
        while True:
            c = s.recv(8192)
            if not c:
                break
            resp += c
            if len(resp) > 60000:
                break
    except socket.timeout:
        pass
    s.close()
    return resp

# reflection list_services: "*" -> proto: field 3 string = 0x1A 0x01 0x2A
msg = b"\x1a\x01*"
for port in [23456, 30001]:
    try:
        r = h2_grpc("::1", port, "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo", msg)
        print("reflection v1alpha port %d: len=%d first=%r" % (port, len(r), r[:400]), flush=True)
    except Exception as e:
        print("reflection v1alpha port %d ERR: %s" % (port, e), flush=True)
    try:
        r = h2_grpc("::1", port, "/grpc.reflection.v1.ServerReflection/ServerReflectionInfo", msg)
        print("reflection v1 port %d: len=%d first=%r" % (port, len(r), r[:400]), flush=True)
    except Exception as e:
        print("reflection v1 port %d ERR: %s" % (port, e), flush=True)

print("===== [4] health check + 常见 gRPC 路径 =====", flush=True)
for port in [23456, 30001]:
    for path in ["/grpc.health.v1.Health/Check",
                 "/grpc.health.v1.Health/Watch",
                 "/grpc.health.v1alpha.Health/Check"]:
        try:
            r = h2_grpc("::1", port, path, b"")
            print("port %d %s -> len=%d first=%r" % (port, path, len(r), r[:200]), flush=True)
        except Exception as e:
            print("port %d %s ERR %s" % (port, path, e), flush=True)

print("===== [5] 二进制认证相关字符串 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
for kw in [b"sign", b"nonce", b"timestamp", b"ed25519", b"Verify", b"publicKey", b"privateKey",
           b"x509", b"ecdsa", b"rsa", b"hmac", b"auth", b"bearer", b"cookie", b"secret",
           b"expiry", b"expire", b"allowed", b"permission", b"sudo", b"root"]:
    ms = re.findall(rb"[\x20-\x7e]{0,70}" + kw + rb"[\x20-\x7e]{0,70}", b)
    print("KW %-12r: %d hits" % (kw, len(ms)), flush=True)
    for m in ms[:5]:
        print("    %r" % m.decode('latin1'), flush=True)
'''
run_cmd(sid, SCAN, "curl-h2-grpc-reflection", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
