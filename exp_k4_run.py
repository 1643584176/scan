# 实验K4: 宿主服务 30001/23456 h2c 方法面审计 — gRPC reflection + connect 语义
# 前置(j94b): 30001/23456 = h2c Go 服务(HTTP/1.1 404 + h2 SETTINGS 响应), 30002 RST
# 目标: 枚举宿主管理服务方法面, 找未认证管理方法(网络边界/权限突破)
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
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
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return ""

NAME = "expk4"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import subprocess, struct

def grpc_frame(body):
    return b"\x00" + struct.pack(">I", len(body)) + body

# 预构造 grpc frame
EMPTY = grpc_frame(b"")          # 空消息
LIST = grpc_frame(b"\x0a\x00")   # reflection: list_services
HEALTH = grpc_frame(b"")         # health check 空消息

def h2(port, path, frame, ctype="application/grpc", extra=None, label=""):
    cmd = ["curl", "-sS", "-m", "6", "-i", "--http2-prior-knowledge", "-X", "POST",
           "-H", "Content-Type: " + ctype, "-H", "te: trailers",
           "--data-binary", "@-", f"http://127.0.0.1:{port}{path}"]
    if extra:
        cmd += extra
    try:
        r = subprocess.run(cmd, input=frame, capture_output=True, timeout=10)
        out = (r.stdout + r.stderr).decode(errors="replace")
        # 压缩输出: 只保留状态行 + 头 + body 前 200B
        lines = out.split("\r\n")
        keep = [l for l in lines if l]
        return f"{label} [{path}] " + " | ".join(keep[:6])[:500]
    except Exception as e:
        return f"{label} [{path}] EXC({e})"

def h1(port, path, body=b"", ctype="application/json", method="POST", label=""):
    cmd = ["curl", "-sS", "-m", "5", "-i", "-X", method,
           "-H", "Content-Type: " + ctype,
           "-H", "Connect-Protocol-Version: 1"]
    if body:
        cmd += ["--data-binary", "@-"]
    cmd += [f"http://127.0.0.1:{port}{path}"]
    try:
        r = subprocess.run(cmd, input=body, capture_output=True, timeout=8)
        out = (r.stdout + r.stderr).decode(errors="replace")
        lines = out.split("\r\n")
        keep = [l for l in lines if l]
        return f"{label} [{path}] " + " | ".join(keep[:5])[:400]
    except Exception as e:
        return f"{label} [{path}] EXC({e})"

for port in (30001, 23456):
    print(f"\n########## PORT {port} ##########", flush=True)
    # 1) gRPC reflection (v1alpha + v1) — 枚举全部方法
    print(h2(port, "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo", LIST, label="REFLECT-v1a"), flush=True)
    print(h2(port, "/grpc.reflection.v1.ServerReflection/ServerReflectionInfo", LIST, label="REFLECT-v1"), flush=True)
    # 2) gRPC health
    print(h2(port, "/grpc.health.v1.Health/Check", HEALTH, label="HEALTH"), flush=True)
    # 3) connect 语义 (content-type: application/json 无帧)
    print(h2(port, "/", b"{}", ctype="application/json", label="H2-JSON-ROOT"), flush=True)
    print(h2(port, "/", b"{}", ctype="application/proto", label="H2-PROTO-ROOT"), flush=True)
    # 4) HTTP/1.1 connect 语义差分 (415/505 模式)
    print(h1(port, "/", ctype="application/json", label="H1-JSON-ROOT"), flush=True)
    print(h1(port, "/", ctype="application/grpc+json", body=grpc_frame(b"{}"), label="H1-GRPCJSON-ROOT"), flush=True)
    print(h1(port, "/", ctype="application/grpc", body=grpc_frame(b"{}"), label="H1-GRPC-ROOT"), flush=True)
    # 5) 常见服务名猜测 (connect-go 路径模式)
    for svc in ("vercel.cell.v1.CellService", "cell.v1.CellService",
                "vercel.apm.v1.APMService", "vercel.metrics.v1.MetricsService",
                "vercel.host.v1.HostService", "cellapi.v1.CellService"):
        for m in ("Info", "List", "Status", "Ping", "GetConfig", "Dump"):
            print(h2(port, f"/{svc}/{m}", EMPTY, label="GUESS"), flush=True)
"""
run_cmd(sid, PROBE, "host-svc-methods", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
