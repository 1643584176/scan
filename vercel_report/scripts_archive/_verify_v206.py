# -*- coding: utf-8 -*-
"""宿主侧: 用 v206 捕获的 (ts, sig, body) 验证 Ed25519 签名内容格式
样本: echo/ls/pwd 三种 body, 每组尝试多种消息组合"""
import base64, hashlib

PUB_B64 = 'RlOG5oHi9BXW4sVwyPlM9yghnU24vW8zvI2aJZZQD7M='
PUB = base64.b64decode(PUB_B64)

p = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493


def sha512(s):
    return hashlib.sha512(s).digest()


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


def ed25519_verify(pub, sig, msg):
    if len(sig) != 64:
        return False
    R = point_decompress(sig[:32])
    if R is None:
        return False
    S = int.from_bytes(sig[32:], 'little')
    if S >= L:
        return False
    A = point_decompress(pub)
    if A is None:
        return False
    k = int.from_bytes(sha512(sig[:32] + pub + msg), 'little') % L
    SB = point_mul(S, B)
    RkA = point_add(R, point_mul(k, A))
    return point_compress(SB) == point_compress(RkA)


# 样本: (ts, sig_b64, body_hex, command)
samples = [
    ('1788232472', 'aqOi2dOnW9Ro3EGT3BzppW9f5tsPoekXwy09TKVB7P42kmFwHmkU9YN+pM/MOCNfl5WpSipwsfV4+Z18EOorBA==',
     '00000000230a046563686f120a68656c6c6f2d76323036220f2f76657263656c2f73616e64626f78', 'echo'),
    ('1788232506', 'A/VgmHvRSBiJoBBxoKSk6IsdBpsLKQY8/S1w/BaHtvrwju46aDmNAtVT8ZmO/qCzwRBpakpiP5oRzz1K/VOzCQ==',
     '000000001b0a026c7312042f746d70220f2f76657263656c2f73616e64626f78', 'ls'),
    ('1788232522', 'qMwwcApTlqRidX/PF/SovC9nSOxJOEbYb2SsU+Jtiuvt/rTiOQtaWkL69qMvJ2CPp3EOPdrCqMMJdrxNYak7CA==',
     '00000000160a03707764220f2f76657263656c2f73616e64626f78', 'pwd'),
]
REQLINE = 'POST /vercel.sandbox.spawn.v1.SpawnService/Spawn HTTP/1.1'
HDRS = REQLINE + '\r\nHost: unix\r\nContent-Type: application/connect+json\r\nConnect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\nX-Timestamp: %s\r\nX-Signature: %s\r\n\r\n'
path = '/vercel.sandbox.spawn.v1.SpawnService/Spawn'

def varint(n):
    out = b''
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            out += bytes([b])
            return out


ts_int = 1788232472
print('PUB len=%d' % len(PUB))
for ts, sigb64, bodyhex, cmdname in samples:
    sig = base64.b64decode(sigb64)
    body = bytes.fromhex(bodyhex)
    tsb = ts.encode()
    proto = body[4:]  # 去掉 4 字节长度前缀
    ts_int = int(ts)
    print('sample %s ts=%s body=%d sig=%d' % (cmdname, ts, len(body), len(sig)))
    variants = {
        'ts': tsb,
        'ts+body': tsb + body,
        'ts+proto': tsb + proto,
        'proto+ts': proto + tsb,
        'body+ts': body + tsb,
        'path+ts': path.encode() + tsb,
        'path+ts+body': path.encode() + tsb + body,
        'path+ts+proto': path.encode() + tsb + proto,
        'ts+path': tsb + path.encode(),
        'ts+path+body': tsb + path.encode() + body,
        'ts+path+proto': tsb + path.encode() + proto,
        'body': body,
        'proto': proto,
        'path': path.encode(),
        'path+body+ts': path.encode() + body + tsb,
        'path+proto+ts': path.encode() + proto + tsb,
        'POST+path+ts': (REQLINE).encode() + tsb,
        'ts+body+path': tsb + body + path.encode(),
        'ts+cmd': tsb + cmdname.encode(),
        'cmd+ts': cmdname.encode() + tsb,
        'proto-ts': bytes([0x0a]) + bytes([len(ts)]) + tsb,
        'ts-int64le': ts_int.to_bytes(8, 'little'),
        'ts-int64be': ts_int.to_bytes(8, 'big'),
        'ts-varint': varint(ts_int),
        'tsvarint+proto': varint(ts_int) + proto,
        'tsint64le+proto': ts_int.to_bytes(8, 'little') + proto,
        'proto-tsfield': bytes([0x08]) + varint(ts_int) + proto,
        'tsn+proto': tsb + b'\n' + proto,
        'proton+ts': proto + b'\n' + tsb,
        'ts-space-proto': tsb + b' ' + proto,
        'path-ts-space-proto': path.encode() + b' ' + tsb + b' ' + proto,
        'reqline-ts': REQLINE.encode() + b'\r\n' + tsb,
        'reqline-ts-proto': REQLINE.encode() + b'\r\n' + tsb + b'\r\n' + proto,
        'ts-proto-field10': b'\x52' + varint(len(tsb)) + tsb,  # field10 string
    }
    for name, msg in variants.items():
        ok = ed25519_verify(PUB, sig, msg)
        if ok:
            print('  *** MATCH: %s' % name)
    print()
print('DONE')
