# -*- coding: utf-8 -*-
"""OAuth 流程黑盒: sign-in/social redirectTo 处理 / state 格式 / 回调端点
重点: redirectTo 是否任意域(白名单为空 + allow_localhost) -> 开放重定向"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def req(method, path, body=None, headers=None, raw_headers=False):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    hdrs = r.headers
    conn.close()
    if raw_headers:
        return st, raw, hdrs
    return st, raw

print('=== [1] sign-in/social 基础行为 ===')
variants = [
    ('google 无 redirectTo', '/neondb/auth/sign-in/social?provider=google'),
    ('google + evil redirectTo', '/neondb/auth/sign-in/social?provider=google&redirectTo=https://evil.com/phish'),
    ('google + localhost redirectTo', '/neondb/auth/sign-in/social?provider=google&redirectTo=http://localhost:3000/dash'),
    ('google + protocol-relative', '/neondb/auth/sign-in/social?provider=google&redirectTo=//evil.com'),
    ('github + evil', '/neondb/auth/sign-in/social?provider=github&redirectTo=https://evil.com'),
    ('无效 provider', '/neondb/auth/sign-in/social?provider=discord&redirectTo=https://evil.com'),
    ('callbackURL 参数', '/neondb/auth/sign-in/social?provider=google&callbackURL=https://evil.com'),
]
for tag, p in variants:
    st, raw, hdrs = req('GET', p, raw_headers=True)
    loc = hdrs.get('location')
    body_s = raw.decode(errors='replace')[:150]
    print('\n[%s] -> %d' % (tag, st))
    if loc:
        print('  Location: %s' % loc[:300])
    else:
        print('  body: %s' % body_s)
    time.sleep(0.4)

print('\n=== [2] POST sign-in/social ===')
for p, b in [('/neondb/auth/sign-in/social', {'provider': 'google', 'redirectTo': 'https://evil.com'}),
             ('/neondb/auth/sign-in/social', {'provider': 'google', 'callbackURL': 'https://evil.com'})]:
    st, raw, hdrs = req('POST', p, b, raw_headers=True)
    loc = hdrs.get('location')
    print('[POST %s %s] -> %d' % (p.split('/')[-1], list(b.keys()), st))
    if loc:
        print('  Location: %s' % loc[:300])
    else:
        print('  body: %s' % raw.decode(errors='replace')[:200])
    time.sleep(0.4)

print('\n=== [3] 回调端点 ===')
for p in ('/neondb/auth/callback/google', '/neondb/auth/callback/google?code=x&state=y',
          '/neondb/auth/callback/github', '/neondb/auth/callback/discord',
          '/neondb/auth/oauth2/authorize', '/neondb/auth/oauth/authorize',
          '/neondb/auth/authorize', '/neondb/auth/token?grant_type=authorization_code'):
    st, raw, hdrs = req('GET', p, raw_headers=True)
    loc = hdrs.get('location')
    print('[%s] -> %d %s' % (p.split('/')[-1][:40], st, ('loc=' + loc[:150]) if loc else raw.decode(errors='replace')[:120]))
    time.sleep(0.3)
