# -*- coding: utf-8 -*-
"""端点清单 x evil Origin 全扫(找漏 Origin 校验的状态变更端点)
+ GET /token 对 evil Origin 的 ACAO 反射(跨站读 JWT 可行性)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'

def req(method, path, body=None, headers=None, origin=None, raw_headers=False):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if origin is not None:
        h['Origin'] = origin
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    data = r.read()
    st = r.status
    hdrs = r.headers
    conn.close()
    if raw_headers:
        return st, data, hdrs
    return st, data

# 登录
st, raw, hdrs = req('POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD},
                    origin='http://localhost:3000', raw_headers=True)
cook = '; '.join(c.split(';')[0] for c in hdrs.get_all('set-cookie'))
print('login=%d' % st)

print('\n=== [1] 状态变更端点清单 x evil Origin(403=有校验, 非403=重点复核!) ===')
# (路径, body)——全部用无害/最小 body; evil origin + 真 cookie
EPS = [
    ('POST', '/neondb/auth/sign-out', {}),
    ('POST', '/neondb/auth/update-user', {'name': 'sec-na-2'}),
    ('POST', '/neondb/auth/change-password', {'currentPassword': PWD, 'newPassword': PWD}),
    ('POST', '/neondb/auth/change-email', {'newEmail': EMAIL}),
    ('POST', '/neondb/auth/revoke-sessions', {'token': 'x'}),
    ('POST', '/neondb/auth/revoke-other-sessions', {}),
    ('POST', '/neondb/auth/forget-password', {'email': EMAIL}),
    ('POST', '/neondb/auth/reset-password', {'newPassword': PWD, 'token': 'x'}),
    ('POST', '/neondb/auth/send-verification-email', {}),
    ('POST', '/neondb/auth/verify-email', {'token': 'x'}),
    ('POST', '/neondb/auth/request-email-change', {'newEmail': EMAIL}),
    ('POST', '/neondb/auth/link-social', {}),
    ('POST', '/neondb/auth/unlink-account', {'providerId': 'google'}),
    ('POST', '/neondb/auth/update-email', {'newEmail': EMAIL}),
    ('POST', '/neondb/auth/two-factor/enable', {}),
    ('POST', '/neondb/auth/two-factor/disable', {}),
    ('POST', '/neondb/auth/mfa/verify', {}),
    ('POST', '/neondb/auth/delete-user', {'password': PWD}),
]
# 先假 cookie 探测端点存在性(全 401=存在需认证; 404=不存在)
print('-- 假cookie探测(401=端点存在) --')
for m, p, b in EPS:
    st, raw = req(m, p, b, headers={'Cookie': 'x=1'}, origin='https://evil.com')
    print('  %s %s -> %d %s' % (m, p.replace('/neondb/auth/', ''), st, raw.decode(errors='replace')[:70]))
    time.sleep(0.15)
# 再真 cookie + evil origin(403 INVALID_ORIGIN=有校验)
print('-- 真cookie + evil origin(403=Origin校验生效) --')
for m, p, b in EPS:
    st, raw = req(m, p, b, headers={'Cookie': cook}, origin='https://evil.com')
    body_s = raw.decode(errors='replace')[:80]
    flag = '' if st == 403 else ' <<< 复核!'
    print('  %s %s -> %d %s%s' % (m, p.replace('/neondb/auth/', ''), st, body_s, flag))
    time.sleep(0.15)

print('\n=== [2] GET 敏感端点 x evil Origin ACAO 反射 ===')
# 假 cookie 探测 GET 端点存在性
for p in ('/neondb/auth/token', '/neondb/auth/session', '/neondb/auth/get-session',
          '/neondb/auth/list-sessions', '/neondb/auth/sessions', '/neondb/auth/me'):
    st, raw, hdrs = req('GET', p, headers={'Cookie': 'x=1'}, origin='https://evil.com', raw_headers=True)
    print('  GET %s (fake-cookie) -> %d  ACAO=%s body=%s' % (
        p.split('/')[-1], st, hdrs.get('access-control-allow-origin'), raw.decode(errors='replace')[:60]))
    time.sleep(0.15)
# 真 cookie + evil origin: ACAO 是否反射(可跨站读?)+ 响应内容
st, raw, hdrs = req('GET', '/neondb/auth/token', headers={'Cookie': cook}, origin='https://evil.com', raw_headers=True)
print('  GET /token evil-origin 真cookie -> %d  ACAO=%s creds=%s' % (
    st, hdrs.get('access-control-allow-origin'), hdrs.get('access-control-allow-credentials')))
print('    body=%s' % raw.decode(errors='replace')[:150])
st, raw, hdrs = req('GET', '/neondb/auth/token', headers={'Cookie': cook}, raw_headers=True)  # 无 origin
print('  GET /token no-origin 真cookie -> %d  ACAO=%s' % (st, hdrs.get('access-control-allow-origin')))
st, raw, hdrs = req('GET', '/neondb/auth/token', headers={'Cookie': cook}, origin='http://localhost:3000', raw_headers=True)
print('  GET /token good-origin -> %d  ACAO=%s' % (st, hdrs.get('access-control-allow-origin')))

print('\n=== [3] 无 Origin 的 POST 状态变更(浏览器顶级表单提交场景) ===')
for m, p, b in [('POST', '/neondb/auth/sign-out', {}), ('POST', '/neondb/auth/update-user', {'name': 'sec-na-2'})]:
    st, raw = req(m, p, b, headers={'Cookie': cook})
    print('  %s %s no-origin -> %d %s' % (m, p.replace('/neondb/auth/', ''), st, raw.decode(errors='replace')[:80]))
