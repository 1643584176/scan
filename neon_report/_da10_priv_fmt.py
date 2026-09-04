# -*- coding: utf-8 -*-
"""离线分析 privateKey 格式(读 _neonauth_priv.txt,全本地)
目标:定位 32B Ed25519 seed,派生公钥与已知 x 对照"""
import json, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

raw = open(r'D:\scan\neon_report\_neonauth_priv.txt', encoding='utf-8').read().strip()
print('file len:', len(raw))
s = raw.strip('"')
print('inner len:', len(s), 'all-hex:', all(c in '0123456789abcdef' for c in s.lower()))
b = bytes.fromhex(s)
print('bytes len:', len(b))
print('head hex:', b[:32].hex())
print('tail hex:', b[-32:].hex())

target_x = 'T2bvRniQ-dVtriL1EY22pby24AQVsi22hGWV8i4aYtY'

def x_of(seed):
    pk = Ed25519PrivateKey.from_private_bytes(seed).public_key()
    return base64.urlsafe_b64encode(
        pk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode().rstrip('=')

# 1) 32B 窗口扫描
hits = []
for off in range(0, len(b) - 31):
    if x_of(b[off:off + 32]) == target_x:
        hits.append(off)
print('\nwindow hits at offsets:', hits)
if hits:
    off = hits[0]
    print('layout: off=%d -> %d extra-before, %d extra-after' % (off, off, len(b) - off - 32))
    print('before hex:', b[:off].hex() if off else '')
    print('after  hex:', b[off + 32:].hex())

# 2) 若没有,尝试 len==64 假设:seed=前32B, 对照 pub 后32B
if not hits and len(b) == 64:
    print('try seed=first32:')
    print('  match x:', x_of(b[:32]) == target_x)
if not hits:
    # 3) hex 串内嵌入 b64url d 的可能: 打印可打印区
    printable = ''.join(chr(c) if 32 <= c < 127 else '.' for c in b)
    print('\nprintable map head 300:', printable[:300])
