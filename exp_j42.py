# 实验J42: HTTP/2 能力侦察 + 23456 端口身份确认
# 目标: 沙箱内可用工具, 二进制中端口字符串, HTTP/2 握手, gRPC 反射
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

NAME = "expj42"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import socket, re, os, subprocess, shutil

print("===== [1] 可用工具 =====", flush=True)
for tool in ["curl", "wget", "nc", "ncat", "socat", "openssl", "go", "grpcurl",
             "python3", "busybox", "nmap", "telnet"]:
    p = shutil.which(tool)
    print("%-10s %s" % (tool, p if p else "NOT FOUND"), flush=True)
try:
    import curl_cffi; print("curl_cffi: yes", flush=True)
except Exception: print("curl_cffi: no", flush=True)
for mod in ["h2", "grpc", "httpx", "hyperframe", "http2"]:
    try:
        __import__(mod); print("py %s: yes" % mod, flush=True)
    except Exception:
        print("py %s: no" % mod, flush=True)
if shutil.which("curl"):
    print(subprocess.run(["curl", "--version"], capture_output=True, text=True).stdout[:400], flush=True)

print("===== [2] 二进制中端口字符串 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
for port in [b"23456", b"30001", b"30002", b"8080", b"80", b"443"]:
    for m in re.finditer(re.escape(port), b):
        s, e = max(0, m.start()-60), min(len(b), m.end()+60)
        ctx = b[s:e]
        # 只打印可打印上下文
        if all(32 <= c < 127 or c in (10, 13, 9) for c in ctx):
            print("port %s @ %d: %r" % (port.decode(), m.start(), ctx.decode('latin1')), flush=True)

print("===== [3] HTTP/2 preface 探测 (23456 TCP) =====", flush=True)
for ip, port in [("::1", 23456), ("127.0.0.1", 23456), ("::1", 30001), ("::1", 30002)]:
    try:
        s = socket.socket(socket.AF_INET6 if ":" in ip else socket.AF_INET)
        s.settimeout(3)
        s.connect((ip, port))
        s.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
        d = s.recv(4096)
        print("%s:%d h2 preface -> %r" % (ip, port, d[:300]), flush=True)
        s.close()
    except Exception as e:
        print("%s:%d h2 preface -> ERR %s" % (ip, port, e), flush=True)

print("===== [4] 纯 python HTTP/2 最小握手 (23456) =====", flush=True)
# 发送 client preface + SETTINGS, 读取服务端 SETTINGS
try:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(("::1", 23456))
    preface = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
    settings = b"\x00\x00\x00\x04\x00\x00\x00\x00\x00"  # empty SETTINGS, len=0
    s.sendall(preface + settings)
    d = s.recv(8192)
    print("server response: %r" % d[:500], flush=True)
    if d:
        # 解析帧: 第一个 SETTINGS
        if len(d) >= 9:
            flen = int.from_bytes(d[0:3], "big")
            ftype = d[3]
            flags = d[4]
            print("frame: len=%d type=%d flags=%d" % (flen, ftype, flags), flush=True)
            if ftype == 4:  # SETTINGS
                print("server SETTINGS ACK:", flush=True)
                for i in range(0, flen, 6):
                    k = int.from_bytes(d[9+i:9+i+2], "big")
                    v = int.from_bytes(d[9+i+2:9+i+6], "big")
                    print("  setting %d = %d" % (k, v), flush=True)
    s.close()
except Exception as e:
    print("h2 handshake ERR: %s" % e, flush=True)

print("===== [5] gRPC 反射请求 (手工 HTTP/2 HEADERS) =====", flush=True)
# 用最小 HTTP/2 帧发 HEADERS (stream 1) 到 grpc reflection
try:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(("::1", 23456))
    s.sendall(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    s.recv(8192)  # server SETTINGS
    # HEADERS 帧: type=1, flags=0x4 (END_HEADERS), stream=1
    # HPACK 编码最小 header block (伪头: :method POST, :path /grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo, :scheme http, :authority localhost, content-type application/grpc, te trailers)
    # 用静态表索引压缩:
    #   :method POST   -> 0x83 (index 3)
    #   :scheme http   -> 0x86 (index 6)
    #   :path (literal, incremental) -> 0x40 | 0x08: len=66? 太长手动构造
    def hpack_literal(idx, val):
        # literal with incremental indexing, indexed name
        h = idx << 4 | 0x00 | 0x40  # 0x40 + idx<<4 不对; literal w/ indexing: 01xxxxxx
        return bytes([0x40 | (idx & 0x3F)]) + bytes([len(val)]) + val
    path = b"/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo"
    authority = b"localhost"
    hb = b""
    hb += b"\x83"                                  # :method POST (static idx 3)
    hb += b"\x86"                                  # :scheme http (static idx 6)
    hb += hpack_literal(1, path)                   # :path
    hb += hpack_literal(2, authority)              # :authority
    hb += b"\x40" + bytes([22]) + b"application/grpc"  # content-type literal
    hb += b"\x40" + bytes([8]) + b"trailers"       # te
    hdr = b"\x00\x00" + len(hb).to_bytes(2, "big") + b"\x01\x04\x00\x00\x00\x01" + hb
    # DATA 帧: gRPC reflection request (空 message: 5-byte prefix 0)
    data = b"\x00\x00\x00\x00\x00"
    dframe = b"\x00\x00" + len(data).to_bytes(2, "big") + b"\x00\x00\x00\x00\x00\x01" + data
    s.sendall(hdr + dframe)
    s.settimeout(4)
    resp = b""
    try:
        while True:
            c = s.recv(8192)
            if not c:
                break
            resp += c
            if len(resp) > 30000:
                break
    except socket.timeout:
        pass
    print("gRPC reflection resp len=%d first=%r" % (len(resp), resp[:600]), flush=True)
    s.close()
except Exception as e:
    print("gRPC probe ERR: %s" % e, flush=True)
'''
run_cmd(sid, SCAN, "h2-capability-recon", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
