# -*- coding: utf-8 -*-
"""external provider 切换触发 Data API 重配 → JWKS 立即刷新?成功后跑 RLS 矩阵"""
import psycopg, json, uuid, base64, time, http.client, ssl
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
key = json.load(open('_apikey.json', encoding='utf-8'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None, tmo=25):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def da_get(tok, path='/neondb/rest/v1/'):
    conn = http.client.HTTPSConnection(DA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    conn.request('GET', path, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:300]

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
conn.commit(); conn.close()
print('key ready:', kid, flush=True)

def make_jwt(payload):
    h = b64u(json.dumps({'alg': 'EdDSA', 'typ': 'JWT', 'kid': kid}).encode())
    p = b64u(json.dumps(payload).encode())
    sig = priv.sign((h + '.' + p).encode())
    return h + '.' + p + '.' + b64u(sig)

now = int(time.time())
tok_owner = make_jwt({'sub': 'u1', 'role': 'neondb_owner', 'iat': now, 'exp': now + 7200})

# 2) 切 external(googleapis 白名单)
st, raw = req('POST', '/projects/%s/jwks' % P, {
    'jwks_url': 'https://www.googleapis.com/oauth2/v3/certs', 'provider_name': 'tmp-switch'})
print('[switch ext] -> %d | %s' % (st, raw[:200].decode(errors='replace')), flush=True)
ext_id = json.loads(raw).get('jwks', {}).get('id', '') if st == 201 else ''
time.sleep(3)
st, raw = da_get(tok_owner)
print('[ext mode, our jwt] -> %d | %s' % (st, raw.decode(errors='replace')[:150]), flush=True)

# 3) 删除 external 回 neon_auth
if ext_id:
    st2, raw2 = req('DELETE', '/projects/%s/jwks/%s' % (P, ext_id))
    print('[delete ext] -> %d' % st2, flush=True)
    time.sleep(3)
    # 4) 立即测我们的 key(期望 Data API 重配后 fetch 到新 key)
    st, raw = da_get(tok_owner)
    print('[back to neon_auth, our jwt] -> %d | %s' % (st, raw.decode(errors='replace')[:150]), flush=True)
else:
    print('switch failed, skip', flush=True)

# 5) 若签名已过(非 400 jwk not found)→ 跑矩阵
if st not in (400, 401, 403) or b'jwk not found' not in raw:
    tests = [
        ('anonymous', {'sub': 'u1', 'role': 'anonymous', 'iat': now, 'exp': now + 3600}),
        ('authenticated', {'sub': 'u1', 'role': 'authenticated', 'iat': now, 'exp': now + 3600}),
        ('authenticator', {'sub': 'u1', 'role': 'authenticator', 'iat': now, 'exp': now + 3600}),
        ('neondb_owner', {'sub': 'u1', 'role': 'neondb_owner', 'iat': now, 'exp': now + 3600}),
        ('cloud_admin', {'sub': 'u1', 'role': 'cloud_admin', 'iat': now, 'exp': now + 3600}),
        ('no role claim', {'sub': 'u1', 'iat': now, 'exp': now + 3600}),
    ]
    for name, pl in tests:
        t = make_jwt(pl)
        st2, raw2 = da_get(t, '/neondb/rest/v1/demo_rls?select=id,secret')
        print('[MATRIX %s] -> %d | %s' % (name, st2, raw2.decode(errors='replace')[:250]), flush=True)
        time.sleep(1)
else:
    print('still jwk not found after switch - cache not refreshed by provider switch', flush=True)

# 6) 清理
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS public.demo_rls')
cur.execute('DELETE FROM neon_auth.jwks WHERE id=%s', (kid,))
conn.commit(); conn.close()
print('cleaned', flush=True)
