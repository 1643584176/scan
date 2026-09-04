# -*- coding: utf-8 -*-
"""验证:错误签名被拒?neonauth 域名在白名单?然后清理"""
import psycopg, json, uuid, base64, time, http.client, ssl
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def make_jwt(priv, payload, kid):
    h = b64u(json.dumps({'alg': 'EdDSA', 'typ': 'JWT', 'kid': kid}).encode())
    p = b64u(json.dumps(payload).encode())
    sig = priv.sign((h + '.' + p).encode())
    return h + '.' + p + '.' + b64u(sig)

def da_get(tok):
    conn = http.client.HTTPSConnection(DA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    conn.request('GET', '/neondb/rest/v1/', headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:200]

# 读回我们的 key(在 DB 里的私钥行,我们插入时用的是自己 seed hex)
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute("SELECT id, \"publicKey\" FROM neon_auth.jwks WHERE \"publicKey\" LIKE '%%my%%' OR id IN (SELECT id FROM neon_auth.jwks WHERE \"createdAt\" > now() - interval '10 minutes' ORDER BY \"createdAt\" DESC LIMIT 3)")
rows = cur.fetchall()
print('recent jwks rows:', [(str(r[0])[:8], str(r[1])[:40]) for r in rows], flush=True)
# 找我们插的行:publicKey 里 x=lV-Mcz... 或刚插入的
cur.execute('SELECT id, "publicKey" FROM neon_auth.jwks ORDER BY "createdAt" DESC LIMIT 1')
myid, mypub = cur.fetchone()
print('latest key id:', myid, flush=True)
conn.close()

# 从 DB 取回我们的 seed:我们插入时 privateKey='"<seed hex>"',需要查
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('SELECT "privateKey" FROM neon_auth.jwks WHERE id=%s', (myid,))
pkv = cur.fetchone()[0]
conn.close()
print('priv stored:', str(pkv)[:60], flush=True)
seed_hex = str(pkv).strip('"')
mypriv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex[:64]))
print('recovered my key', flush=True)

now = int(time.time())
# 1) 正确签名(role=neondb_owner)
tok = make_jwt(mypriv, {'sub': 'x', 'role': 'neondb_owner', 'iat': now, 'exp': now + 3600}, str(myid))
st, raw = da_get(tok)
print('[valid sig role=owner] -> %d | %s' % (st, raw.decode(errors='replace')), flush=True)

# 2) 错误签名(随机 key,同 kid)
evil = Ed25519PrivateKey.generate()
tok2 = make_jwt(evil, {'sub': 'x', 'role': 'neondb_owner', 'iat': now, 'exp': now + 3600}, str(myid))
st, raw = da_get(tok2)
print('[wrong sig] -> %d | %s' % (st, raw.decode(errors='replace')), flush=True)

# 3) 无 kid(仅 iat/exp)
tok3 = make_jwt(mypriv, {'sub': 'x', 'role': 'neondb_owner', 'iat': now, 'exp': now + 3600}, 'nonexistent-kid')
st, raw = da_get(tok3)
print('[valid sig unknown kid] -> %d | %s' % (st, raw.decode(errors='replace')), flush=True)

# 4) neonauth URL 白名单测试
def req(method, path, body=None, tmo=20):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=tmo)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

st, raw = req('POST', '/projects/%s/jwks' % P, {
    'jwks_url': 'https://ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build/neondb/auth/.well-known/jwks.json',
    'provider_name': 'pna'})
print('\n[neonauth in whitelist?] -> %d | %s' % (st, raw[:250].decode(errors='replace')), flush=True)

# 5) 清理:删我们插入的 key
if st == 201:
    st2, raw2 = req('DELETE', '/projects/%s/jwks/%s' % (P, json.loads(raw).get('jwks', {}).get('id', '')))
    print('cleanup whitelist-provider ->', st2, flush=True)
conn = psycopg.connect(URI, connect_timeout=20)
cur = conn.cursor()
cur.execute('DELETE FROM neon_auth.jwks WHERE id=%s', (myid,))
conn.commit()
conn.close()
print('deleted my jwks row', flush=True)
