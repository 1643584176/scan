# 实验J11: agent 请求完整捕获 - hex dump + 头名提取
# J10 抓到: POST .../Ping HTTP/1.1 + timestamp=1787132361(秒) 紧贴路径
# 目标: ① dump timestamp 附近 ±600B 原始 hex+ascii(找 signature 头名和值)
#       ② 找 "signature" 在堆段(0x3f69b0... 区域) 的命中, dump 上下文
#       ③ 找 "grpc+json" 附近完整请求头块
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

stop = threading.Event()
reported = set()

def scan_for(targets, label):
    """在全部可读段搜索 target, dump ±600B hex+ascii"""
    maps = get_maps()
    n = 0
    for start, end in maps:
        size = min(end - start, 16 * 1024 * 1024)
        d = read_mem_segment(start, size)
        if not d:
            continue
        for pat in targets:
            i = 0
            while True:
                i = d.find(pat, i)
                if i < 0:
                    break
                abs_off = start + i
                # 只报堆段(0x300000000000 以上, 二进制 rodata 在 0x10000000 以下)
                if abs_off > 0x300000000000 and abs_off not in reported:
                    reported.add(abs_off)
                    ctx = d[max(0, i-600):i+600]
                    print(f"\n=== {label} HIT @0x{abs_off:x} ===", flush=True)
                    print(hexdump(ctx, abs_off - 600), flush=True)
                    n += 1
                    if n >= 30:
                        return n
                i += 1
    return n

def worker():
    """循环扫描: timestamp 特征(1787 开头 10 位数字) + signature + grpc+json"""
    ts_pat = re.compile(rb"1787\d{6}")
    while not stop.is_set():
        maps = get_maps()
        for start, end in maps:
            size = min(end - start, 16 * 1024 * 1024)
            d = read_mem_segment(start, size)
            if not d:
                continue
            # 1. timestamp 数字
            for m in ts_pat.finditer(d):
                abs_off = start + m.start()
                if abs_off > 0x300000000000 and abs_off not in reported:
                    reported.add(abs_off)
                    ctx = d[max(0, m.start()-600):m.start()+600]
                    print(f"\n=== TS HIT @0x{abs_off:x} ===", flush=True)
                    print(hexdump(ctx, abs_off - 600), flush=True)
            # 2. signature 头(找 "signature" 或 "Signature" 或 "X-Signature")
            for pat in (b"signature", b"Signature", b"signature ", b"signature:"):
                i = d.find(pat)
                if i >= 0:
                    abs_off = start + i
                    if abs_off > 0x300000000000 and abs_off not in reported:
                        reported.add(abs_off)
                        ctx = d[max(0, i-600):i+900]
                        print(f"\n=== SIG HIT @0x{abs_off:x} ===", flush=True)
                        print(hexdump(ctx, abs_off - 600), flush=True)
        time.sleep(0.05)

print("== 启动扫描 ==", flush=True)
t = threading.Thread(target=worker, daemon=True)
t.start()
deadline = time.time() + 110
while time.time() < deadline:
    time.sleep(1)
stop.set()
time.sleep(0.3)
print(f"done, reported={len(reported)}", flush=True)
