# -*- coding: utf-8 -*-
"""补测: cookie-as-token 单测 + keycloak register 403 响应头(CF?) + /login 页面"""
import http.client, ssl, json, re, time

ctx = ssl.create_default_context()
HOST = 'console-stage.neon.build'

def raw_req(host, method, path, headers=None, body=None, port=443):
    try:
        conn = http.client.HTTPSConnection(host, port, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
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

# 1. GET / 拿 cookie
st, hdrs, body = raw_req(HOST, 'GET', '/')
csrf = ''
for part in hdrs.get('set-cookie', '').split(','):
    kv = part.strip().split(';')[0]
    if kv.startswith('_gorilla_csrf='):
        csrf = kv.split('=', 1)[1]
print('csrf len:', len(csrf), flush=True)

# 2. cookie-as-token 重测(带重试)
for attempt in range(2):
    st, h2, b2 = raw_req(HOST, 'POST', '/api/register',
                         {'Content-Type': 'application/json',
                          'Origin': 'https://console-stage.neon.build',
                          'Referer': 'https://console-stage.neon.build/',
                          'Cookie': '_gorilla_csrf=%s' % csrf,
                          'X-CSRF-Token': csrf},
                         json.dumps({'email': 'libobo1229+secctl@gmail.com',
                                     'password': 'SecTest!2026pass2'}).encode())
    print('[cookie-as-token #%d] -> %d %s' % (attempt, st, b2[:500].replace('\n', ' ')), flush=True)
    if h2.get('location'):
        print('  LOCATION: %s' % h2['location'], flush=True)
    time.sleep(1)

# 3. /login 页面(csrf meta?)
st, hdrs, body = raw_req(HOST, 'GET', '/login')
print('\n[GET /login] %d loc=%s' % (st, hdrs.get('location', '')), flush=True)
m = re.search(r'csrf-token" content="([^"]+)"', body)
print('  csrf meta:', (m.group(1)[:50] + '...') if m else 'NONE', flush=True)

# 4. keycloak register 403 响应头判断(CF?)
st, hdrs, body = raw_req(HOST, 'GET', '/auth/keycloak/register')
print('\n[kc register] %d' % st, flush=True)
for k in ['server', 'cf-ray', 'cf-cache-status', 'x-powered-by']:
    if k in hdrs:
        print('  %s: %s' % (k, hdrs[k]), flush=True)
