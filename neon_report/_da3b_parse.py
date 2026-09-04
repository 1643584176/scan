# -*- coding: utf-8 -*-
"""解析 neon_auth.jwks privateKey 存储格式(打码输出)
尝试:1) 前 64 hex 作 seed 派生公钥 vs jwks x;2) 全串 hex->bytes 扫描可打印区"""
import psycopg, json, base64

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()
cur.execute('SELECT "publicKey", "privateKey" FROM neon_auth.jwks LIMIT 1')
pub_jwk, priv_jwk = cur.fetchone()
conn.close()
print('priv len:', len(priv_jwk))
s = priv_jwk.strip('"')
print('stripped len:', len(s), 'ishex:', all(c in '0123456789abcdef' for c in s.lower()))

# 尝试1: 前 64 hex 作 seed
try:
    seed = bytes.fromhex(s[:64])
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    pk = Ed25519PrivateKey.from_private_bytes(seed).public_key()
    x = base64.urlsafe_b64encode(pk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode().rstrip('=')
    pj = json.loads(pub_jwk)
    print('seed(64hex) derived x == jwks x:', x == pj['x'])
except Exception as e:
    print('try1 err:', e)

# 尝试2: 整体 hex->bytes,扫可打印 JSON 片段
try:
    b = bytes.fromhex(s)
    print('bytes len:', len(b))
    # 找 '{' 位置
    starts = [i for i in range(len(b)) if b[i] == 0x7b]
    print('0x7b positions:', starts[:10])
    if starts:
        seg = b[starts[0]:starts[0]+200]
        printable = ''.join(chr(c) if 32 <= c < 127 else '.' for c in seg)
        print('segment:', printable[:180])
except Exception as e:
    print('try2 err:', e)

# 尝试3: 也许 d 字段就在 hex 里: 打印最后 96 hex 是什么
print('tail 96:', s[-96:])
print('head 96:', s[:96])
