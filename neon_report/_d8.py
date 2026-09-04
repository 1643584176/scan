# -*- coding: utf-8 -*-
"""Data API RLS 语义测试:建表+RLS,用自签不同 role JWT 查询"""
import psycopg, json, uuid, base64, time, http.client, ssl
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'

# 1) PG 建测试表 + RLS
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute("SELECT rolname, rolbypassrls FROM pg_roles WHERE rolname IN ('neondb_owner','anonymous','authenticated','authenticator','neon_auth')")
print('bypassrls:', cur.fetchall(), flush=True)
cur.execute('DROP TABLE IF EXISTS public.demo_rls')
cur.execute('CREATE TABLE public.demo_rls (id serial PRIMARY KEY, secret text)')
cur.execute('INSERT INTO public.demo_rls (secret) VALUES (\'s1\'), (\'s2\'), (\'s3\')')
cur.execute('ALTER TABLE public.demo_rls ENABLE ROW LEVEL SECURITY')
cur.execute('CREATE POLICY deny_all ON public.demo_rls FOR SELECT USING (false)')
cur.execute('GRANT SELECT ON public.demo_rls TO anonymous, authenticated, authenticator')
conn.commit()
print('table demo_rls ready (RLS deny_all, 3 rows)', flush=True)
conn.close()

# 2) 生成密钥对插入 jwks(标准流程)
priv = Ed25519PrivateKey.generate()
seed = priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
kid = str(uuid.uuid4())
x = base64.urlsafe_b64encode(pub).rstrip(b'=').decode()
pub_jwk = json.dumps({'crv': 'Ed25519', 'x': x, 'kty': 'OKP'})
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('INSERT INTO neon_auth.jwks (id, "publicKey", "privateKey", "createdAt") VALUES (%s, %s, %s, now())',
            (kid, pub_jwk, '"%s"' % seed.hex()))
conn.commit()
conn.close()
print('key inserted:', kid, flush=True)
time.sleep(2)

def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def make_jwt(payload, mykid=kid):
    h = b64u(json.dumps({'alg': 'EdDSA', 'typ': 'JWT', 'kid': mykid}).encode())
    p = b64u(json.dumps(payload).encode())
    sig = priv.sign((h + '.' + p).encode())
    return h + '.' + p + '.' + b64u(sig)

def da(path, tok, method='GET', body=None):
    conn = http.client.HTTPSConnection(DA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    conn.request(method, '/neondb/rest/v1/' + path,
                 body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:400]

now = int(time.time())
# 3) 各角色 JWT 查询 demo_rls
tests = [
    ('anonymous', {'sub': 'u1', 'role': 'anonymous', 'iat': now, 'exp': now + 3600}),
    ('authenticated', {'sub': 'u1', 'role': 'authenticated', 'iat': now, 'exp': now + 3600}),
    ('authenticator', {'sub': 'u1', 'role': 'authenticator', 'iat': now, 'exp': now + 3600}),
    ('neondb_owner', {'sub': 'u1', 'role': 'neondb_owner', 'iat': now, 'exp': now + 3600}),
    ('no role claim', {'sub': 'u1', 'iat': now, 'exp': now + 3600}),
]
for name, pl in tests:
    st, raw = da('demo_rls?select=id,secret', make_jwt(pl))
    print('[%s] GET demo_rls -> %d | %s' % (name, st, raw.decode(errors='replace')[:300]), flush=True)
    time.sleep(0.7)

# 4) 清理
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS public.demo_rls')
cur.execute('DELETE FROM neon_auth.jwks WHERE id=%s', (kid,))
conn.commit()
conn.close()
print('\ncleaned up', flush=True)
