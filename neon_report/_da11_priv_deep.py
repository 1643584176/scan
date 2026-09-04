# -*- coding: utf-8 -*-
"""深度分析:official jwks 行的 privateKey blob(169B)结构
对照:PG publicKey x vs .well-known/jwks.json 实际签发 x;blob 分区假设检验。
零破坏:HTTP GET + 本地计算。"""
import psycopg, json, base64, http.client, ssl
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ctx = ssl.create_default_context()
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def x_of(seed):
    pk = Ed25519PrivateKey.from_private_bytes(seed).public_key()
    return base64.urlsafe_b64encode(
        pk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode().rstrip('=')

# 1) PG 行
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('SELECT id, "publicKey", "privateKey", "expiresAt" FROM neon_auth.jwks ORDER BY "createdAt"')
rows = cur.fetchall()
conn.close()
print('jwks rows:', len(rows))
for rid, pub, priv, exp in rows:
    print('kid:', rid, 'exp:', exp)
    pj = json.loads(pub)
    x_db = pj['x']
    print('  db x:', x_db)
    priv_s = (priv or '').strip().strip('"')
    b = bytes.fromhex(priv_s) if all(c in '0123456789abcdef' for c in priv_s.lower()) else None
    print('  priv inner len:', len(priv_s), '-> bytes:', len(b) if b else 'n/a')

    if b and len(b) > 32:
        # 分区假设: [0:32]=seed_a [32:64]=pub_a?
        print('  b[0:32] as seed -> x:', x_of(b[0:32]))
        print('  b[32:64] hex:', b[32:64].hex())
        # b64url decode x 得到 raw pub
        pad = '=' * (-len(x_db) % 4)
        raw_pub = base64.urlsafe_b64decode(x_db + pad)
        print('  db raw pub hex:', raw_pub.hex())
        print('  b[32:64] == db raw pub:', b[32:64] == raw_pub)
        # blob 内是否包含 raw pub
        hits = []
        i = b.find(raw_pub)
        while i != -1:
            hits.append(i)
            i = b.find(raw_pub, i + 1)
        print('  raw pub occurrences at:', hits)

# 2) jwks.json 实际签发 key
conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
conn.request('GET', '/neondb/auth/.well-known/jwks.json',
             headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
r = conn.getresponse(); raw = r.read(); st = r.status
conn.close()
print('\njwks.json ->', st)
if st == 200:
    keys = json.loads(raw).get('keys', [])
    print('served keys:', len(keys))
    for k in keys:
        print('  kid:', k.get('kid'), 'x:', k.get('x'))
