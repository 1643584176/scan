# -*- coding: utf-8 -*-
"""1) RFC8032 测试向量自测 verify 实现
2) 用 v205/v206/v207 样本验证更多签名格式组合"""
import base64, hashlib

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


# ===== RFC 8032 TEST 1 =====
pub1 = bytes.fromhex('d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a')
sig1 = bytes.fromhex('e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b')
print('RFC8032 TEST1:', ed25519_verify(pub1, sig1, b''))

# ===== RFC 8032 TEST 2 =====
pub2 = bytes.fromhex('3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c')
sig2 = bytes.fromhex('92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00')
print('RFC8032 TEST2:', ed25519_verify(pub2, sig2, bytes(range(1, 129))))

# ===== v205/v206/v207 样本 =====
PUB_B64 = 'RlOG5oHi9BXW4sVwyPlM9yghnU24vW8zvI2aJZZQD7M='
PUB = base64.b64decode(PUB_B64)

# (ts, sig_b64, body_hex)
samples = [
    ('1788232195', 'JTaYw1xwi//FtVYx1pdXudGsJXXzMOxj3uwILNAuXh4IVYB6gfX3/srgLQZ9g/M+fj/jtqIi0YHQ7ojaO/21DA==', ''),
    ('1788232472', 'aqOi2dOnW9Ro3EGT3BzppW9f5tsPoekXwy09TKVB7P42kmFwHmkU9YN+pM/MOCNfl5WpSipwsfV4+Z18EOorBA==', '00000000230a046563686f120a68656c6c6f2d76323036220f2f76657263656c2f73616e64626f78'),
    ('1788232805', 'zPiO7TSujOs+hmuh0mzr9y2WNUl5QPfACzcXIKYyvtpXFgQG/IJ1flsOCBHqvqdbss0IknOa35CXJidXXHnXAw==', ''),
]
path = '/vercel.sandbox.spawn.v1.SpawnService/Spawn'
path2 = 'vercel.sandbox.spawn.v1.SpawnService/Spawn'

import time as _t


def rfc3339(ts):
    return _t.strftime('%Y-%m-%dT%H:%M:%SZ', _t.gmtime(int(ts)))


def varint(n):
    out = b''
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


print()
for ts, sigb64, bodyhex in samples:
    sig = base64.b64decode(sigb64)
    tsb = ts.encode()
    tsi = int(ts)
    body = bytes.fromhex(bodyhex) if bodyhex else b''
    proto = body[4:] if body else b''
    variants = {
        'ts': tsb,
        'ts+nl': tsb + b'\n',
        'ts+path': tsb + path.encode(),
        'path+ts': path.encode() + tsb,
        'path2+ts': path2.encode() + tsb,
        'path+colon+ts': path.encode() + b':' + tsb,
        'ts+colon+path': tsb + b':' + path.encode(),
        'colon-ts': b':' + tsb,
        'POST+path+ts': ('POST %s' % path).encode() + tsb,
        'rfc3339': rfc3339(ts).encode(),
        'rfc3339+path': rfc3339(ts).encode() + path.encode(),
        'path+rfc3339': path.encode() + rfc3339(ts).encode(),
        'int64le': tsi.to_bytes(8, 'little'),
        'int64be': tsi.to_bytes(8, 'big'),
        'int64le+path': tsi.to_bytes(8, 'little') + path.encode(),
        'path+int64le': path.encode() + tsi.to_bytes(8, 'little'),
        'varint': varint(tsi),
        'path+varint': path.encode() + varint(tsi),
        'proto-ts-path': b'\x0a' + varint(len(tsb)) + tsb + b'\x12' + varint(len(path.encode())) + path.encode(),
        'tsb+proto': tsb + proto,
        'proto+tsb': proto + tsb,
        'path+tsb+proto': path.encode() + tsb + proto,
        'ts-ms': str(tsi * 1000).encode(),
        'hex-ts': hex(tsi).encode(),
        'ts-float': ('%d.0' % tsi).encode(),
    }
    hits = []
    for name, msg in variants.items():
        if ed25519_verify(PUB, sig, msg):
            hits.append(name)
    print('sample ts=%s hits: %s' % (ts, hits or 'NONE'))
print('DONE')
