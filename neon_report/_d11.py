# -*- coding: utf-8 -*-
"""RLS 语义测试 v3:后台轮询等 JWKS 缓存刷新后跑角色矩阵"""
import psycopg, json, uuid, base64, time, http.client, ssl
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ctx = ssl.create_default_context()
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'

# 1) 表 + key
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS public.demo_rls')
cur.execute('CREATE TABLE public.demo_rls (id serial PRIMARY KEY, secret text)')
cur.execute("INSERT INTO public.demo_rls (secret) VALUES ('s1'), ('s2'), ('s3')")
cur.execute('ALTER TABLE public.demo_rls ENABLE ROW LEVEL SECURITY')
cur.execute('CREATE POLICY deny_all ON public.demo_rls FOR SELECT USING (false)')
cur.execute('GRANT SELECT ON public.demo_rls TO anonymous, authenticated, authenticator')

priv = Ed25519PrivateKey.generate()
seed = priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
kid = str(uuid.uuid4())
x = base64.urlsafe_b64encode(pub).rstrip(b'=').decode()
cur.execute('INSERT INTO neon_auth.jwks (id, "publicKey", "privateKey", "createdAt") VALUES (%s, %s, %s, now())',
            (kid, json.dumps({'crv': 'Ed25519', 'x': x, 'kty': 'OKP'}), '"%s"' % seed.hex()))
conn.commit()
conn.close()
print('table + key ready:', kid, flush=True)

def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def make_jwt(payload):
    h = b64u(json.dumps({'alg': 'EdDSA', 'typ': 'JWT', 'kid': kid}).encode())
    p = b64u(json.dumps(payload).encode())
    sig = priv.sign((h + '.' + p).encode())
    return h + '.' + p + '.' + b64u(sig)

def da(path, tok):
    conn = http.client.HTTPSConnection(DA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    conn.request('GET', '/neondb/rest/v1/' + path, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:300]

now0 = int(time.time())
# 2) 轮询等缓存刷新(最多 10 分钟)
ready = False
for attempt in range(13):
    tok = make_jwt({'sub': 'u1', 'role': 'neondb_owner', 'iat': now0, 'exp': now0 + 7200})
    st, raw = da('demo_rls?select=id,secret', tok)
    elapsed = int(time.time()) - now0
    print('[poll %d @%ds] -> %d | %s' % (attempt, elapsed, st, raw.decode(errors='replace')[:120]), flush=True)
    if st != 400 or b'jwk not found' not in raw:
        ready = True
        break
    time.sleep(45)

if ready:
    # 3) 完整矩阵
    now = int(time.time())
    tests = [
        ('anonymous', {'sub': 'u1', 'role': 'anonymous', 'iat': now, 'exp': now + 3600}),
        ('authenticated', {'sub': 'u1', 'role': 'authenticated', 'iat': now, 'exp': now + 3600}),
        ('authenticator', {'sub': 'u1', 'role': 'authenticator', 'iat': now, 'exp': now + 3600}),
        ('neondb_owner', {'sub': 'u1', 'role': 'neondb_owner', 'iat': now, 'exp': now + 3600}),
        ('cloud_admin', {'sub': 'u1', 'role': 'cloud_admin', 'iat': now, 'exp': now + 3600}),
        ('no role claim', {'sub': 'u1', 'iat': now, 'exp': now + 3600}),
    ]
    for name, pl in tests:
        st, raw = da('demo_rls?select=id,secret', make_jwt(pl))
        print('[MATRIX %s] -> %d | %s' % (name, st, raw.decode(errors='replace')[:250]), flush=True)
        time.sleep(1)
else:
    print('cache not refreshed in time', flush=True)

# 4) 清理
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS public.demo_rls')
cur.execute('DELETE FROM neon_auth.jwks WHERE id=%s', (kid,))
conn.commit()
conn.close()
print('cleaned', flush=True)
