# -*- coding: utf-8 -*-
"""插入自己的 Ed25519 keypair 到 neon_auth.jwks -> JWKS 端点同步?-> 自签 JWT 打 Data API"""
import psycopg, json, uuid, base64, time, http.client, ssl
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ctx = ssl.create_default_context()
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'

# 1) 生成自己的 keypair
priv = Ed25519PrivateKey.generate()
seed = priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
kid = str(uuid.uuid4())
x = base64.urlsafe_b64encode(pub).rstrip(b'=').decode()
d = base64.urlsafe_b64encode(seed).rstrip(b'=').decode()
pub_jwk = json.dumps({'crv': 'Ed25519', 'x': x, 'kty': 'OKP'})
print('my kid:', kid, flush=True)
print('my x:', x, flush=True)

conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute("SELECT \"publicKey\" FROM neon_auth.jwks WHERE id=%s", (kid,))
if cur.fetchone() is None:
    cur.execute('INSERT INTO neon_auth.jwks (id, "publicKey", "privateKey", "createdAt") VALUES (%s, %s, %s, now())',
                (kid, pub_jwk, '"%s"' % seed.hex()))
    conn.commit()
    print('inserted my key', flush=True)
conn.close()

time.sleep(2)

# 2) JWKS 端点是否同步
def na_get(path):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
    conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:800]

st, raw = na_get('/neondb/auth/.well-known/jwks.json')
print('\n[jwks.json] -> %d' % st, flush=True)
print(raw.decode(errors='replace'), flush=True)
keys = json.loads(raw).get('keys', [])
print('keys count:', len(keys), flush=True)
mine = [k for k in keys if k.get('kid') == kid]
print('my key in jwks endpoint:', bool(mine), flush=True)

# 3) 若同步 -> 自签 JWT 打 Data API
if mine:
    def b64u(b):
        return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
    now = int(time.time())
    for role in ['neondb_owner', 'cloud_admin', 'authenticated']:
        header = {'alg': 'EdDSA', 'typ': 'JWT', 'kid': kid}
        payload = {'sub': 'sec-self', 'role': role, 'iat': now, 'exp': now + 3600}
        h = b64u(json.dumps(header).encode())
        p = b64u(json.dumps(payload).encode())
        sig = priv.sign((h + '.' + p).encode())
        tok = h + '.' + p + '.' + b64u(sig)
        conn = http.client.HTTPSConnection(DA, context=ctx, timeout=20)
        conn.request('GET', '/neondb/rest/v1/', headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                                                          'Authorization': 'Bearer ' + tok})
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        print('[DA role=%s] -> %d | %s' % (role, st, raw[:250].decode(errors='replace')), flush=True)
        time.sleep(0.8)
