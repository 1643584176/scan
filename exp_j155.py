# 实验J155: 完整提取 sandbox-init(0x400000-0xe9e000) + Go symbol表 + 深度strings分析
# j154: /proc/1/mem 权限OK, 提取因进度打印bug中断在4MB; 确认Go静态二进制+connect-go
# 方法: 修复后完整提取; 解析ELF段; gopclntab符号提取; 关键词上下文
# 零破坏: 纯内存读取
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

NAME = "expj155"
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

CA = r'''
import os, struct
out = open("/tmp/d155a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def read_mem(addr, size):
    f = os.open("/proc/1/mem", os.O_RDONLY)
    try:
        os.lseek(f, addr, 0)
        d = os.read(f, size)
        return d
    finally:
        os.close(f)
# 提取 0x400000 ~ 0xe9e000
dst = open("/tmp/sinit.bin", "wb")
total = 0
addr = 0x400000
end = 0x00e9e000
CH = 0x1000
while addr < end:
    d = read_mem(addr, CH)
    if not d:
        p("short_read_at", hex(addr))
        break
    dst.write(d)
    addr += len(d)
    total += len(d)
dst.close()
p("extracted_total", total)
p("=== DONE")
out.close()
'''

CB = r'''
import re, struct
out = open("/tmp/d155b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
data = open("/tmp/sinit.bin", "rb").read()
p("size", len(data))

# ---- ELF section headers ----
def elf_sections(d):
    if d[:4] != b"\x7fELF":
        return []
    is64 = d[4] == 2
    endian = "<" if d[5] == 1 else ">"
    if is64:
        e_shoff = struct.unpack_from(endian + "Q", d, 0x28)[0]
        e_shentsize = struct.unpack_from(endian + "H", d, 0x3A)[0]
        e_shnum = struct.unpack_from(endian + "H", d, 0x3C)[0]
        e_shstrndx = struct.unpack_from(endian + "H", d, 0x3E)[0]
        shstr_off = struct.unpack_from(endian + "Q", d, e_shoff + e_shstrndx * e_shentsize + 0x18)[0]
        secs = []
        for i in range(e_shnum):
            off = e_shoff + i * e_shentsize
            name_off = struct.unpack_from(endian + "I", d, off)[0]
            sh_type = struct.unpack_from(endian + "I", d, off + 4)[0]
            flags = struct.unpack_from(endian + "Q", d, off + 8)[0]
            addr = struct.unpack_from(endian + "Q", d, off + 0x10)[0]
            offset = struct.unpack_from(endian + "Q", d, off + 0x18)[0]
            size = struct.unpack_from(endian + "Q", d, off + 0x20)[0]
            name = b""
            j = shstr_off + name_off
            while j < len(d) and d[j] != 0:
                name += bytes([d[j]])
                j += 1
            secs.append((name.decode("latin1"), sh_type, hex(addr), offset, size))
        return secs
    return []

secs = elf_sections(data)
p("=== SECTIONS ===")
for nm, t, addr, off, sz in secs:
    p(nm, t, addr, off, sz)

# ---- Go buildinfo ----
p("=== BUILDINFO ===")
i = data.find(b"\xff Go buildinf:")
if i > 0:
    p("found_at", hex(i))
    # 读构建信息后的版本字符串
    j = i + len(b"\xff Go buildinf:")
    v = b""
    while j < len(data) and data[j] != 0 and len(v) < 200:
        v += bytes([data[j]])
        j += 1
    p("buildinfo", v[:200])

# ---- gopclntab 函数名 ----
p("=== GOPCLNTAB ===")
idx = data.find(b"\xfb\xff\xff\xff\x00\x00")
if idx < 0:
    idx = data.find(b"\xf1\xff\xff\xff\x00\x00")
if idx > 0:
    # Go 1.20+: pcHeader{magic(4) pad1(1) pad2(1) minLC(1) ptrSize(1) nfunc(4) nfiles(4) textStart(8) funcnameOffset(4) cuOffset(4) filetabOffset(4) pctabOffset(4) funcDataOffset(4)}
    off = idx - 0x10
    nfunc = struct.unpack_from("<I", data, off + 8)[0]
    p("pcHeader_at", hex(idx), "nfunc", nfunc)
    # 跳过 header(0x30) 找到 functab (由 pctabOffset 指示)
    # 简化: 用 go tool 不可用, 直接提取所有看起来像函数名的字符串(含 . 的)
    names = re.findall(rb"[a-z0-9_\./]+\.\([\*a-zA-Z0-9_\.]+\)[a-zA-Z0-9_\.]*|[a-z0-9_\./]+\.[A-Z][a-zA-Z0-9_\.]*", data)
    uniq = {}
    for n in names:
        t = n.decode("latin1")
        uniq[t] = uniq.get(t, 0) + 1
    p("funcname_candidates", len(uniq))
    # 过滤出高价值包
    interesting = []
    for t in sorted(uniq.keys()):
        if any(k in t for k in ["vercel", "sandbox", "cell", "cmd", "command", "exec", "run",
                                "auth", "token", "sign", "verify", "socket", "proxy", "forward",
                                "mount", "network", "policy", "secret", "key", "pubkey",
                                "ed25519", "tls", "cert", "http", "grpc", "connect", "rpc",
                                "shell", "spawn", "pid", "syscall", "ioctl", "loop"]):
            interesting.append(t)
    p("=== FUNCS ===")
    for t in interesting[:500]:
        p("F:", t[:160])
else:
    p("no_gopclntab")

# ---- 关键字符串上下文 ----
p("=== KEY_CTX ===")
for kw in [b"init.sock", b"pubkey", b"signature", b"verify", b"command", b"--socket", b"--pubkey",
           b"vercel-proxy-ca", b"ca-cert.pem", b"oidc", b"metadata", b"169.254", b"100.64"]:
    i = data.find(kw)
    if i >= 0:
        p("K:", kw, "@", hex(i), repr(data[max(0, i - 80):i + 200]))
    else:
        p("K:", kw, "NOT_FOUND")
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "full-extract", timeout=280)
catfile(sid, "/tmp/d155a.txt", "d155a", 2000)

run_cmd(sid, CB, "deep-analysis", timeout=280)
catfile(sid, "/tmp/d155b.txt", "d155b", 15000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
