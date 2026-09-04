# -*- coding: utf-8 -*-
"""keycloak 标准注册路径探测:注册是否开放(realm config)
GET /realms/staging-realm/protocol/openid-connect/registrations?..."""
import http.client, ssl, urllib.parse, re

ctx = ssl.create_default_context()
HOST = 'console-stage.neon.build'

def raw_req(path, headers=None, method='GET', body=None):
    try:
        conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        if headers:
            h.update(headers)
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        raw = r.read()
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        st = r.status
        conn.close()
        return st, hdrs, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, {}, 'EXC %s' % e

params = urllib.parse.urlencode({
    'client_id': 'neon-console',
    'redirect_uri': 'https://console-stage.neon.build/auth/keycloak/callback',
    'response_type': 'code', 'scope': 'openid profile email',
    'state': 'x',
})
st, hdrs, body = raw_req('/realms/staging-realm/protocol/openid-connect/registrations?' + params)
print('[registrations] %d' % st, flush=True)
print(' loc=%s' % hdrs.get('location', ''), flush=True)
low = body.lower()
if 'register' in low and 'form' in low or 'kc-register' in low:
    print('  => registration form PRESENT (realm registration allowed)', flush=True)
    # 提取 form action(拿 session 提交点)
    m = re.search(r'<form[^>]*id="kc-register-form"[^>]*action="([^"]+)"', body)
    if m:
        print('  form action:', m.group(1)[:200], flush=True)
elif 'challenge' in low or 'cf-chl' in low or 'cloudflare' in low and 'just a moment' in low:
    print('  => CF challenge page', flush=True)
else:
    print('  body head:', body[:300].replace('\n', ' '), flush=True)

# 对照:登录页状态(同路径 auth)
st, hdrs, body = raw_req('/realms/staging-realm/protocol/openid-connect/auth?' + params)
print('\n[auth page] %d' % st, flush=True)
low = body.lower()
print('  kc-login form:', 'kc-login' in low, '| register link:', 'register' in low, flush=True)
m = re.search(r'href="([^"]*register[^"]*)"', body)
if m:
    print('  register link:', m.group(1)[:200], flush=True)
