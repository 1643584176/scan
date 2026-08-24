# 实验J23: 127.0.0.1 端口扫描(netns 共享 -> VM 管理面?) + vda 挂载文件读取 + vda 读取速度测试
# J7: /proc/1/net/unix 可见 cell/apm/metrics socket -> netns 与 VM 共享
# 目标: 找 VM(celld) 监听在 loopback 的服务 -> guest OS 管理面
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

NAME = "expj23"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# [1] loopback 端口扫描(快速, 前 20000 + 常用高位)
SCAN = r'''
import socket, concurrent.futures, time
def check(p):
    s = socket.socket()
    s.settimeout(0.15)
    try:
        if s.connect_ex(("127.0.0.1", p)) == 0:
            return p
    except Exception:
        pass
    finally:
        s.close()
    return None
ports = list(range(1, 20001)) + [2375,2376,5000,8080,8443,9000,9090,10000,30000,50000,65534,65535]
open_ports = []
t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(400) as ex:
    for r in ex.map(check, ports):
        if r:
            open_ports.append(r)
print("scan_time", round(time.time()-t0,1), "open:", open_ports, flush=True)
'''
run_cmd(sid, SCAN, "portscan", wait=True, timeout=120000)

# [2] 若开放端口, HTTP banner
PROBE = r'''
import socket
open_ports = [p for p in range(1,65536) if False]
# 用 /proc/net/tcp 直接看监听
import re
print("=== /proc/net/tcp LISTEN ===")
for line in open("/proc/net/tcp"):
    parts = line.split()
    if len(parts) > 3 and parts[3] == "0A":
        lp = parts[1].split(":")[1]
        port = int(lp, 16)
        print("LISTEN 127.0.0.1:", port)
for line in open("/proc/net/tcp6"):
    parts = line.split()
    if len(parts) > 3 and parts[3] == "0A":
        lp = parts[1].split(":")[1]
        port = int(lp, 16)
        print("LISTEN ::1:", port)
'''
run_cmd(sid, PROBE, "listen-tab", wait=True, timeout=30000)

# [3] vda 挂载文件 + 读取速度
FILES = r'''
import time
print("=== /etc/hosts ===")
print(open("/etc/hosts").read())
print("=== /etc/resolv.conf ===")
print(open("/etc/resolv.conf").read())
print("=== vda 读取速度测试(32MB) ===")
t0 = time.time()
with open("/dev/vda","rb") as f:
    f.seek(64*1024*1024)
    d = f.read(32*1024*1024)
dt = time.time()-t0
print("read 32MB:", round(dt,2), "s =", round(32/dt,1), "MB/s")
print("sample:", d[:64].hex())
'''
run_cmd(sid, FILES, "files-speed", wait=True, timeout=60000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
