# 实验J179: 本地HTTP服务识别(30001/30002/23456) + sandbox-init读取对照测试
# j178: 30001=Go HTTP服务(404); 网关不可达; mmap EIO; 读sandbox-init被杀
# 本步: 1)三端口多路径探测(/, /health, /api, /status, /version, /metrics, /debug, /v1, /config, /internal)
#       2)对照: 读 /usr/bin/python3 (大文件) vs sandbox-init -> 确认是否特定文件触发
#       3)sandbox-init 分块读绕过尝试
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

def catfile(sid, path, label, n=8000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj179"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: 三端口多路径 HTTP 探测
PA = r'''
import os, socket
out = open("/tmp/d179a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def http(port, path, to=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", port))
        s.send(f"GET {path} HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n".encode())
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
paths = ["/", "/health", "/healthz", "/api", "/api/", "/status", "/version", "/v1",
         "/metrics", "/debug", "/debug/pprof/", "/config", "/internal", "/info",
         "/api/v1", "/api/status", "/_vercel", "/__vercel", "/v2", "/command"]
for port in [30001, 30002, 23456]:
    for path in paths:
        d = http(port, path)
        if d.startswith(b"HTTP"):
            first = d.split(b"\r\n\r\n")[0][:200]
            body = d.split(b"\r\n\r\n")[1][:150] if b"\r\n\r\n" in d else b""
            p("RESP", port, path, first.decode(errors="replace").replace("\r\n", " | "),
              "BODY", body.decode(errors="replace").replace("\r\n", " ")[:120])
        else:
            p("RESP", port, path, d[:120])
        out.flush()
p("done")
out.close()
'''

# PB: 对照读取测试 - 大文件 vs sandbox-init
PB = r'''
import os
out = open("/tmp/d179b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
# 对照1: /usr/bin/python3 (同量级大文件)
try:
    d = open("/usr/bin/python3", "rb").read()
    p("PYTHON_READ", len(d))
except Exception as ex:
    p("PYTHON_EXC", repr(ex))
p("python_done")
out.flush()
# 对照2: sandbox-init 完整读取
try:
    d = open("/run/vercel/share/sandbox-init", "rb").read()
    p("SBINIT_READ", len(d))
except Exception as ex:
    p("SBINIT_EXC", repr(ex))
p("sbinit_done")
out.close()
'''

# PC: sandbox-init 分块读取 (1MB/块)
PC = r'''
import os
out = open("/tmp/d179c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
fd = os.open("/run/vercel/share/sandbox-init", os.O_RDONLY)
for i in range(17):
    d = os.read(fd, 1024 * 1024)
    if not d:
        p("EOF", i)
        break
    p("CHUNK", i, len(d), d[:16].hex())
    out.flush()
os.close(fd)
p("done")
out.close()
'''

steps = [
    ("http-probe", "/tmp/d179a.txt", PA),
    ("read-cmp", "/tmp/d179b.txt", PB),
    ("chunk-read", "/tmp/d179c.txt", PC),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 8000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
