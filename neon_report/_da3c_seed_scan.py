# -*- coding: utf-8 -*-
"""暴力偏移扫描:169B 中任意 32B 窗口作 Ed25519 seed,派生公钥对比 jwks x"""
import psycopg, json, base64

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()
cur.execute('SELECT "publicKey", "privateKey" FROM neon_auth.jwks LIMIT 1')
pub_jwk, priv_jwk = cur.fetchone()
conn.close()

s = priv_jwk.strip('"')
b = bytes.fromhex(s)
pj = json.loads(pub_jwk)
target_x = pj['x']
print('bytes len:', len(b), 'target x:', target_x[:16], '...')

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def x_of(seed):
    pk = Ed25519PrivateKey.from_private_bytes(seed).public_key()
    return base64.urlsafe_b64encode(
        pk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode().rstrip('=')

hit = []
# 窗口扫描(所有 32B 起点)
for off in range(0, len(b) - 31):
    if x_of(b[off:off+32]) == target_x:
        hit.append(('window', off))
        break
print('32B window scan hit:', hit)

# 也试倒序/异或种子?先试每 2 字节跳过(若 hex 间插)
for step in (1, 2):
    for off in range(0, min(16, len(b) - 63), step):
        cand = b[off:off+64:2] if step == 2 else None
        if step == 1:
            continue
        if len(cand) == 32 and x_of(cand) == target_x:
            hit.append(('step2', off))
            break
print('extra hits:', hit)

# 打印前 48B 与 141 附近的内容(hex 形式,供人工判断)
print('b[0:48] hex:', b[:48].hex())
print('b[100:169] hex:', b[100:].hex())
