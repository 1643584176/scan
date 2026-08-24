# 实验J156: sandbox-init 深度分析修正版 (避免灾难回溯, 正确解析gopclntab/buildinfo)
# j155: 提取11.1MB成功; 复杂regex回溯卡死CPU被杀; gopclntab/buildinfo解析偏移错误
# 方法: 简单迭代扫描字符串; Go1.20+ pcHeader正确偏移; 分段分析
# 零破坏: 纯本地内存分析
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

NAME = "expj156"
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

# cmdA: 重新提取 (沙箱重启后 /proc/1/mem 是新实例)
CA = r'''
import os
out = open("/tmp/d156a.txt", "w")
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
dst = open("/tmp/sinit.bin", "wb")
total = 0
addr = 0x400000
end = 0x00e9e000
CH = 0x1000
while addr < end:
    d = read_mem(addr, CH)
    if not d:
        p("short_at", hex(addr))
        break
    dst.write(d)
    addr += len(d)
    total += len(d)
dst.close()
p("extracted_total", total)
p("=== DONE")
out.close()
'''

# cmdB: buildinfo + gopclntab (Go 1.20+)
CB = r'''
import struct
out = open("/tmp/d156b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
data = open("/tmp/sinit.bin", "rb").read()
p("size", len(data))

# ---- Go buildinfo 解析 ----
p("=== BUILDINFO ===")
i = data.find(b"\xff Go buildinf:")
if i > 0:
    p("bi_at", hex(i))
    # header: magic(1) ptrSize(1) 然后 "Go buildinf:" 已含; 接着 ver 字符串
    # 格式: \xff Go buildinf:\x00 <ptrSize> <magic2字节> <version string>
    j = i + len(b"\xff Go buildinf:")
    if j < len(data):
        p("after_header", data[j:j+4].hex())
        # version 字符串通常跟在这些字节后
        k = j + 4
        s = b""
        while k < len(data) and data[k] not in (0, 0x20) and len(s) < 300:
            s += bytes([data[k]])
            k += 1
        p("version", s[:300])
        # 再找 0x20 分隔的后续字符串 (模块路径)
        mods = []
        k2 = k + 1
        while k2 < len(data) and len(mods) < 10:
            if data[k2] == 0:
                break
            e = data.find(b"\x00", k2)
            if e < 0 or e - k2 > 500:
                break
            t = data[k2:e]
            if len(t) > 5:
                mods.append(t)
            k2 = e + 1
        p("mods", mods[:10])

# ---- gopclntab 解析 (Go 1.20+ 布局) ----
p("=== GOPCLNTAB ===")
for magic, name in [(b"\xf1\xff\xff\xff\x00\x00\x00\x00", "1.20+"), (b"\xf0\xff\xff\xff\x00\x00\x00\x00", "1.18-1.19")]:
    idx = data.find(magic)
    if idx < 0:
        p("magic", name, "not found")
        continue
    p("magic", name, "at", hex(idx))
    nfunc = struct.unpack_from("<I", data, idx + 8)[0]
    nfiles = struct.unpack_from("<I", data, idx + 12)[0]
    text_start = struct.unpack_from("<Q", data, idx + 16)[0]
    fn_off = struct.unpack_from("<I", data, idx + 24)[0]
    p("nfunc", nfunc, "nfiles", nfiles, "textStart", hex(text_start))
    # funcname table 起始 = idx + fn_off
    # 函数名以 \x00 结尾连续存放
    ftab = idx + fn_off
    names = []
    k = ftab
    while k < len(data) and len(names) < 200000:
        e = data.find(b"\x00", k)
        if e < 0:
            break
        nm = data[k:e]
        k = e + 1
        if len(nm) >= 3:
            names.append(nm)
        if k - ftab > 3000000:
            break
    p("name_count", len(names))
    interesting = []
    for nm in names:
        try:
            t = nm.decode("latin1")
        except Exception:
            continue
        if any(x in t.lower() for x in ["vercel", "sandbox", "cell", "cmd", "command", "exec",
                                        "run", "auth", "token", "sign", "verify", "socket",
                                        "proxy", "forward", "mount", "policy", "secret", "key",
                                        "pubkey", "ed25519", "tls", "cert", "connect", "rpc",
                                        "shell", "spawn", "syscall", "ioctl", "loop", "http",
                                        "grpc", "command"]):
            interesting.append(t)
    p("=== FUNCS ===")
    for t in interesting[:600]:
        p("F:", t[:180])
p("=== DONE")
out.close()
'''

# cmdC: 关键字符串上下文 + URL路径模式 (迭代扫描)
CC = r'''
import re
out = open("/tmp/d156c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
data = open("/tmp/sinit.bin", "rb").read()
p("=== KEY_CTX ===")
for kw in [b"init.sock", b"pubkey", b"--socket", b"--pubkey", b"vercel-proxy-ca", b"ca-cert.pem",
           b"oidc", b"metadata", b"169.254", b"100.64", b"vercel.com", b"api.vercel", b"signature",
           b"ed25519", b"PRIVATE KEY", b"BEGIN", b"cell.sock", b"containerd", b"apm.sock"]:
    i = data.find(kw)
    if i >= 0:
        p("K:", kw.decode("latin1"), "@", hex(i), repr(data[max(0, i - 60):i + 220]))
    else:
        p("K:", kw.decode("latin1"), "NOT_FOUND")

p("=== URL_PATHS ===")
# 简单扫描 /xxx/yyy 模式 (迭代, 无回溯)
pat = re.compile(rb"/[a-zA-Z0-9._~-]{2,}(?:/[a-zA-Z0-9._~-]{2,}){0,4}")
seen = set()
cnt = 0
for m in pat.finditer(data):
    s = m.group()
    if len(s) < 4:
        continue
    if s in seen:
        continue
    seen.add(s)
    p("U:", s.decode("latin1")[:200])
    cnt += 1
    if cnt > 300:
        break
p("url_count", cnt)

p("=== FLAG_ENV ===")
# 环境变量名模式
pat2 = re.compile(rb"[A-Z][A-Z0-9_]{3,}")
seen2 = set()
cnt2 = 0
for m in pat2.finditer(data):
    s = m.group().decode("latin1")
    if s in seen2:
        continue
    seen2.add(s)
    if any(k in s.lower() for k in ["vercel", "cell", "sandbox", "token", "key", "secret", "auth",
                                    "proxy", "api", "url", "endpoint", "host", "port", "cmd",
                                    "command", "exec", "path", "socket", "tls", "cert"]):
        p("E:", s)
        cnt2 += 1
        if cnt2 > 200:
            break
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "extract", timeout=280)
catfile(sid, "/tmp/d156a.txt", "d156a", 2000)

run_cmd(sid, CB, "gopclntab", timeout=280)
catfile(sid, "/tmp/d156b.txt", "d156b", 15000)

run_cmd(sid, CC, "strctx", timeout=200)
catfile(sid, "/tmp/d156c.txt", "d156c", 15000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
