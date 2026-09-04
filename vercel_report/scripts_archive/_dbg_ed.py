# -*- coding: utf-8 -*-
"""调试 ed25519 verify: RFC8032 TEST2 中间值"""
import hashlib

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


sig = bytes.fromhex('92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00')
pub = bytes.fromhex('3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c')
msg = bytes(range(1, 129))

R = point_decompress(sig[:32])
S = int.from_bytes(sig[32:], 'little')
A = point_decompress(pub)
print('R decompress:', R is not None)
print('S:', S, 'S<L:', S < L)
print('A decompress:', A is not None)
if R and A:
    k = int.from_bytes(sha512(sig[:32] + pub + msg), 'little') % L
    print('k computed')
    SB = point_mul(S, B)
    RkA = point_add(R, point_mul(k, A))
    print('SB == R+kA:', point_compress(SB) == point_compress(RkA))
    print('SB hex:', point_compress(SB).hex()[:16])
    print('RkA hex:', point_compress(RkA).hex()[:16])

# 额外: 用点校验 8*R 和 8*A 是否在曲线上
for name, pt in [('B', B), ('R', R), ('A', A)]:
    if pt is None:
        continue
    x, y = pt
    lhs = (y * y - x * x - 1 - d * x * x * y * y) % p
    print('%s on-curve: %s' % (name, lhs == 0))
