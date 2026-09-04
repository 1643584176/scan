# -*- coding: utf-8 -*-
"""Origin 校验绕过变体矩阵(change-password 同密码探针,零破坏)
+ OPTIONS 预检 ACAO 反射 + /token 安全头 + .well-known 目录"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
EMAIL = 'libobo1229+na2@gmail.com'
PWD = 'SecTest!2026pass2'

def req(method, path, body=None, headers=None, host=NA, include_origin=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if include_origin is not None:
        h['Origin'] = include_origin
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw, r.headers

# 登录
st, raw, hdrs = req('POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD},
                    include_origin='http://localhost:3000')
cks = hdrs.get('set-cookie')
cook = '; '.join(c.split(';')[0] for c in hdrs.get_all('set-cookie')) if hdrs.get('set-cookie') else ''
print('login=%d cookie_len=%d' % (st, len(cook)))

PROBE_BODY = {'currentPassword': PWD, 'newPassword': PWD}

print('\n=== [1] Origin 绕过变体矩阵(探针: change-password 同密码, 200=校验绕过!) ===')
variants = [
    ('good localhost:3000', 'http://localhost:3000'),
    ('no port localhost', 'http://localhost'),
    ('https scheme', 'https://localhost:3000'),
    ('startsWith 子域', 'http://localhost:3000.evil.com'),
    ('startsWith 斜杠', 'http://localhost:3000/evil.com'),
    ('userinfo @evil', 'http://localhost:3000@evil.com'),
    ('userinfo @localhost', 'http://evil.com@localhost:3000'),
    ('尾点 FQDN', 'http://localhost:3000.'),
    ('大写 HOST', 'http://LOCALHOST:3000'),
    ('大写 scheme', 'HTTP://localhost:3000'),
    ('127.0.0.1 映射', 'http://127.0.0.1:3000'),
    ('[::1] IPv6', 'http://[::1]:3000'),
    ('带 path 的 origin', 'http://localhost:3000/anything'),
    ('带 query', 'http://localhost:3000?a=1'),
    ('tab 尾随', 'http://localhost:3000\t'),
    ('evil 端口 3000', 'https://evil.com:3000'),
    ('neonauth 自身域名', 'https://' + NA),
]
for tag, o in variants:
    st, raw, hdrs = req('POST', '/neondb/auth/change-password', PROBE_BODY,
                        headers={'Cookie': cook}, include_origin=o)
    msg = raw.decode(errors='replace')[:90]
    mark = ' <<< BYPASS!' if st == 200 else ''
    print('  [%s] %s -> %d %s%s' % (tag, o, st, msg, mark))
    time.sleep(0.25)

print('\n=== [2] 双 Origin header(服务端取哪个?) ===')
conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
h = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Cookie': cook,
     'Origin': 'https://evil.com'}
conn.putrequest('POST', '/neondb/auth/change-password')
for k, v in h.items():
    conn.putheader(k, v)
conn.putheader('Origin', 'http://localhost:3000')
conn.endheaders(json.dumps(PROBE_BODY).encode())
r = conn.getresponse()
print('  evil+good 双头 -> %d %s' % (r.status, r.read().decode(errors='replace')[:100]))
conn.close()
time.sleep(0.25)
conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
conn.putrequest('POST', '/neondb/auth/change-password')
for k, v in h.items():
    conn.putheader(k, v)
conn.putheader('Origin', 'http://localhost:3000')  # good 在前
conn.endheaders(json.dumps(PROBE_BODY).encode())
r = conn.getresponse()
print('  good+evil 双头 -> %d %s' % (r.status, r.read().decode(errors='replace')[:100]))
conn.close()
time.sleep(0.25)

print('\n=== [3] OPTIONS 预检 + ACAO 反射 ===')
for o in ('http://localhost:3000', 'https://evil.com', 'null'):
    st, raw, hdrs = req('OPTIONS', '/neondb/auth/sign-out', None,
                        headers={'Origin': o, 'Access-Control-Request-Method': 'POST',
                                 'Access-Control-Request-Headers': 'content-type'})
    print('  OPTIONS origin=%s -> %d  ACAO=%s  creds=%s  allow-hdrs=%s' % (
        o, st, hdrs.get('access-control-allow-origin'), hdrs.get('access-control-allow-credentials'),
        hdrs.get('access-control-allow-headers')))
    time.sleep(0.2)

print('\n=== [4] GET /token 响应头(缓存/安全头) ===')
st, raw, hdrs = req('GET', '/neondb/auth/token', headers={'Cookie': cook})
print('  status=%d body=%s' % (st, raw.decode(errors='replace')[:120]))
for k in ('cache-control', 'pragma', 'expires', 'strict-transport-security', 'x-content-type-options',
          'x-frame-options', 'content-security-policy', 'referrer-policy', 'x-powered-by', 'server'):
    print('    %s: %s' % (k, hdrs.get(k)))

print('\n=== [5] .well-known 枚举 ===')
for p in ('openid-configuration', 'jwks.json', 'oauth-authorization-server', 'assetlinks.json',
          'apple-app-site-association', 'security.txt'):
    st, raw, hdrs = req('GET', '/neondb/auth/.well-known/' + p)
    print('  %s -> %d %s' % (p, st, raw.decode(errors='replace')[:120]))
    time.sleep(0.2)

print('\n=== [6] sign-in 无 Origin(登录端点是否需要 Origin) ===')
st, raw, hdrs = req('POST', '/neondb/auth/sign-in/email', {'email': EMAIL, 'password': PWD})
print('  sign-in no-origin -> %d %s' % (st, raw.decode(errors='replace')[:100]))
