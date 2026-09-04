# -*- coding: utf-8 -*-
"""Neon Auth 技术面:cookie 属性 / Origin 校验 / CSRF / redirect 处理"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'

def raw_req(method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    all_hdrs = r.headers
    conn.close()
    return st, raw, all_hdrs

print('=== [1] sign-in 响应头全量(cookie 属性) ===')
st, raw, hdrs = raw_req('POST', '/neondb/auth/sign-in/email',
                        {'email': EMAIL, 'password': PWD},
                        {'Origin': 'http://localhost:3000'})
print('status=%d' % st)
for k, v in hdrs.items():
    if k.lower() in ('set-cookie', 'x-frame-options', 'content-security-policy', 'strict-transport-security', 'access-control-allow-origin', 'access-control-allow-credentials'):
        print('  %s: %s' % (k, v))

# 拿 cookie
cks = hdrs.get_all('Set-Cookie')
cookie_all = '; '.join(c.split(';')[0] for c in cks)
print('\ncookies:', [c.split(';')[0] for c in cks])

print('\n=== [2] Origin 校验矩阵(状态变更: sign-out 带 cookie) ===')
origins = [
    ('无 Origin', None),
    ('localhost:3000', 'http://localhost:3000'),
    ('恶意 evil.com', 'https://evil.com'),
    ('null', 'null'),
    ('https://console-stage.neon.build', 'https://console-stage.neon.build'),
    ('neon.build 子域', 'https://anything.neon.build'),
]
for tag, o in origins:
    hdrs = {'Cookie': cookie_all}
    if o:
        hdrs['Origin'] = o
    st, raw, _ = raw_req('POST', '/neondb/auth/sign-out', {}, hdrs)
    print('  [%s] sign-out -> %d %s' % (tag, st, raw.decode(errors='replace')[:100]))
    time.sleep(0.4)

print('\n=== [3] 重新登录(恢复 session) ===')
st, raw, hdrs = raw_req('POST', '/neondb/auth/sign-in/email',
                        {'email': EMAIL, 'password': PWD},
                        {'Origin': 'http://localhost:3000'})
cks = hdrs.get_all('Set-Cookie')
cookie_all = '; '.join(c.split(';')[0] for c in cks)
print('status=%d' % st)

print('\n=== [4] 状态变更端点 Origin 敏感度 ===')
for path, body in [
    ('/neondb/auth/update-user', {'name': 'sec-na-2'}),
    ('/neondb/auth/change-password', {'currentPassword': PWD, 'newPassword': PWD}),
    ('/neondb/auth/revoke-sessions', {'token': 'x'}),
]:
    st, raw, _ = raw_req('POST', path, body, {'Cookie': cookie_all, 'Origin': 'https://evil.com'})
    print('  [evil origin] %s -> %d %s' % (path, st, raw.decode(errors='replace')[:150]))
    time.sleep(0.4)
    st, raw, _ = raw_req('POST', path, body, {'Cookie': cookie_all, 'Origin': 'http://localhost:3000'})
    print('  [good origin] %s -> %d %s' % (path, st, raw.decode(errors='replace')[:150]))
    time.sleep(0.4)

print('\n=== [5] redirectTo/redirect 参数处理 ===')
for path in ('/neondb/auth/sign-in/email?redirectTo=https://evil.com/phish',
             '/neondb/auth/sign-out?redirectTo=https://evil.com',
             '/neondb/auth/error?redirectTo=https://evil.com'):
    st, raw, hdrs = raw_req('GET', path)
    loc = hdrs.get('location') if hdrs else None
    print('  GET %s -> %d loc=%s body=%s' % (path.split('?')[0], st, loc, raw.decode(errors='replace')[:80]))
