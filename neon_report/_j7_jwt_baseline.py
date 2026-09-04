# -*- coding: utf-8 -*-
"""真 JWT 全量 + Data API 权限基线:根/表清单/方法/角色生效"""
import http.client, ssl, json, time, base64

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
DA_BASE = '/neondb/rest/v1'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'

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

# 登录 + 拿 JWT
st, raw, cookies = req(NA, 'POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD}, origin='http://localhost:3000')
cookie_str_full = '; '.join(c.split(';')[0] for c in cookies) if cookies else ''
st, raw, _ = req(NA, 'GET', '/neondb/auth/token', cookie=cookie_str_full, origin='http://localhost:3000')
jwt_data = json.loads(raw)
jwt = jwt_data.get('token', '')
print('JWT len=%d' % len(jwt))
parts = jwt.split('.')
pad = lambda s: s + '=' * (-len(s) % 4)
print('header:', base64.urlsafe_b64decode(pad(parts[0])).decode())
print('payload:', base64.urlsafe_b64decode(pad(parts[1])).decode())

def da(method, path, body=None, token=jwt):
    return req(DA_HOST, method, DA_BASE + path, body=body, token=token)

print('\n=== Data API 基线(真 JWT) ===')
st, raw, _ = da('GET', '/')
print('root -> %d | %s' % (st, raw.decode(errors='replace')[:600]))
st, raw, _ = da('GET', '/', headers={'Accept': 'application/openapi+json'})
print('openapi -> %d | %s' % (st, raw.decode(errors='replace')[:300]))

print('\n=== 表清单 ===')
# 从 openapi 提取表名
try:
    spec = json.loads(raw)
    for k in spec.get('paths', {}):
        print('  path:', k)
except Exception as e:
    print('  (openapi parse fail:', e, ')', raw.decode(errors='replace')[:200])
