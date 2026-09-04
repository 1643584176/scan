# -*- coding: utf-8 -*-
"""签名格式破解 v2: 同沙箱样本 + session id 组合
v208 沙箱 sbx_5Cco0Ofkw5qA31yxK3HfjsuLEZCp 的 (ts, sig, body)"""
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


PUB = base64.b64decode('RlOG5oHi9BXW4sVwyPlM9yghnU24vW8zvI2aJZZQD7M=')

# v208 沙箱样本 (同沙箱!): ts, sig, body(hex)
samples = [
    ('1788232805', 'zPiO7TSujOs+hmuh0mzr9y2WNUl5QPfACzcXIKYyvtpXFgQG/IJ1flsOCBHqvqdbss0IknOa35CXJidXXHnXAw==',
     '000000002b0a04626173681202632d120e6563686f20763230382d6d61726b220f2f76657263656c2f73616e64626f78', 'sbx_5Cco0Ofkw5qA31yxK3HfjsuLEZCp'),
    ('1788232195', 'JTaYw1xwi//FtVYx1pdXudGsJXXzMOxj3uwILNAuXh4IVYB6gfX3/srgLQZ9g/M+fj/jtqIi0YHQ7ojaO/21DA==', '',
     'sbx_Nfs9xSXxRn2nORKgjEgJXOZNrBqV'),
    ('1788232472', 'aqOi2dOnW9Ro3EGT3BzppW9f5tsPoekXwy09TKVB7P42kmFwHmkU9YN+pM/MOCNfl5WpSipwsfV4+Z18EOorBA==',
     '00000000230a046563686f120a68656c6c6f2d76323036220f2f76657263656c2f73616e64626f78', 'sbx_ljfCdNfwzMAdsC859FrPhWJI1aj8'),
]
path = '/vercel.sandbox.spawn.v1.SpawnService/Spawn'


def varint(n):
    out = b''
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


for ts, sigb64, bodyhex, sid in samples:
    sig = base64.b64decode(sigb64)
    tsb = ts.encode()
    sidb = sid.encode()
    body = bytes.fromhex(bodyhex) if bodyhex else b''
    proto = body[4:] if body else b''
    variants = {
        'ts': tsb,
        'ts+sid': tsb + sidb,
        'sid+ts': sidb + tsb,
        'path+ts': path.encode() + tsb,
        'path+ts+sid': path.encode() + tsb + sidb,
        'ts+sid+path': tsb + sidb + path.encode(),
        'sid+ts+path': sidb + tsb + path.encode(),
        'path+sid+ts': path.encode() + sidb + tsb,
        'ts+colon+sid': tsb + b':' + sidb,
        'sid+colon+ts': sidb + b':' + tsb,
        'ts+sid+proto': tsb + sidb + proto,
        'sid+ts+proto': sidb + tsb + proto,
        'path+ts+sid+proto': path.encode() + tsb + sidb + proto,
        'sid-only': sidb,
        'sid+path+ts': sidb + path.encode() + tsb,
        'ts+proto+sid': tsb + proto + sidb,
        'proto+ts+sid': proto + tsb + sidb,
        'session-varint+ts': b'\x0a' + varint(len(sidb)) + sidb + b'\x12' + varint(len(tsb)) + tsb,
    }
    hits = []
    for name, msg in variants.items():
        if ed25519_verify(PUB, sig, msg):
            hits.append(name)
    print('sid=%s hits: %s' % (sid, hits or 'NONE'))
print('DONE')
