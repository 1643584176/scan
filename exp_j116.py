# 实验J116: interactive 面深挖 — 26661 端口监听地址/可达性 + interactive API 端点枚举
# 动机: j109 留下"interactivePort 26661 入站面(待确认)"; 若 26661 监听非 loopback 且外部可达
#       => 绕过认证直连沙箱 shell 的可能
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

NAME = "expj116"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c, flush=True)
if c != 200:
    print(r[:300], flush=True)
    sys.exit(1)
resp = json.loads(r)
sid = resp["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)
print("create resp keys:", list(resp["sandbox"].keys()), flush=True)
print("interactivePort:", resp["sandbox"].get("interactivePort"), flush=True)

# [A] API: 沙箱详情 + interactive 端点枚举
print("\n== [A] API 详情与 interactive 端点 ==", flush=True)
c, r = api("GET", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print(f"GET /v2/sandboxes/{NAME}: {c}: {r[:500]}", flush=True)

for ep in [
    f"/v2/sandboxes/{NAME}/interactive",
    f"/v2/sandboxes/{NAME}/interactive/url",
    f"/v2/sandboxes/{NAME}/interactive/connect",
    f"/v2/sandboxes/{NAME}/interactive/session",
    f"/v2/sandboxes/{NAME}/interactive/port",
    f"/v2/sandboxes/{NAME}/ports",
    f"/v2/sandboxes/{NAME}/interactivePort",
    f"/v2/sandboxes/sessions/{sid}/interactive",
    f"/v2/sandboxes/sessions/{sid}/interactive/connect",
    f"/v2/sandboxes/sessions/{sid}/interactive/url",
    f"/v2/sandboxes/sessions/{sid}/ports",
    f"/v2/sandboxes/sessions/{sid}/portforward",
    f"/v2/sandboxes/sessions/{sid}/connect",
]:
    for m in ["GET", "POST"]:
        c, r = api(m, f"{ep}?teamId={TEAM}")
        if c != 404:
            print(f"  {m} {ep.split('?')[0]}: {c}: {r[:200]}", flush=True)
print("  (其余 404 未列出)", flush=True)

PROBE = r"""
import socket, subprocess, os

print("== [1] 26661 监听情况 ==", flush=True)
for cmd in [["ss", "-tlnp"], ["ss", "-ulnp"], ["netstat", "-tlnp"]]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if r.stdout.strip():
            print(f"--- {' '.join(cmd)} ---", flush=True)
            print(r.stdout[:1500], flush=True)
            break
    except Exception:
        pass

# 自身 IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("172.31.0.2", 53))
self_ip = s.getsockname()[0]
s.close()
print("self ip:", self_ip, flush=True)

print("\n== [2] TCP 连接矩阵 (26661 与常见 interactive 端口) ==", flush=True)
def tcp_probe(ip, port, label, send=None, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        print(f"  [CONNECT-OK] {label} {ip}:{port}", flush=True)
        if send:
            s.sendall(send)
        s.settimeout(2.5)
        try:
            data = s.recv(2048)
            print(f"    recv {len(data)}B: {data[:120]!r}", flush=True)
        except socket.timeout:
            print("    recv timeout", flush=True)
        s.close()
        return True
    except socket.timeout:
        print(f"  [TIMEOUT] {label} {ip}:{port}", flush=True)
    except OSError as e:
        print(f"  [REFUSED/RST] {label} {ip}:{port}: {e}", flush=True)
    return False

# HTTP/2 前奏 (interactive 可能是 h2)
h2_preface = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
ports = [26661, 26662, 8080, 3000]
for port in ports:
    tcp_probe("127.0.0.1", port, f"loopback:{port}", send=h2_preface)
    tcp_probe(self_ip, port, f"self:{port}", send=h2_preface)

print("\n== [3] 端口范围扫描 26650-26670 (loopback) ==", flush=True)
for port in range(26650, 26671):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.8)
        s.connect(("127.0.0.1", port))
        print(f"  OPEN 127.0.0.1:{port}", flush=True)
        s.close()
    except Exception:
        pass

print("INTERACTIVE_DONE", flush=True)
"""

run_cmd(sid, PROBE, "interactive-probe", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
