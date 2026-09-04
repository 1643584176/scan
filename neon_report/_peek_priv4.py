# -*- coding: utf-8 -*-
import psycopg, json

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('SELECT "publicKey", "privateKey" FROM neon_auth.jwks')
pub, priv = cur.fetchone()
conn.close()

print('publicKey:', pub[:400], flush=True)
s = priv.strip('"')
b = bytes.fromhex(s)
print('\npriv hex len:', len(s), 'blob len:', len(b))
# 分段:每 32B 一段
for i in range(0, len(b), 16):
    seg = b[i:i+16]
    print('  [%3d-%3d] %s' % (i, i + len(seg), seg.hex()), flush=True)
