# -*- coding: utf-8 -*-
"""prod 注册通道探测(只读,不真注册):
1. keycloak prod-realm registrations 页
2. openid-configuration registration_endpoint
3. console /register /signup 页面
4. 关键: Neon 现在注册是否走邀请/白名单
"""
import http.client, ssl, re

ctx = ssl.create_default_context()

def get(host, path, headers=None):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'}
        if headers:
            h.update(headers)
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'ignore'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

print('=== 1. keycloak prod registrations ===', flush=True)
st, raw, hdrs = get('console.neon.tech', '/realms/prod-realm/protocol/openid-connect/registrations')
print('->', st, 'len', len(raw), 'CT', hdrs.get('content-type', '')[:40], flush=True)
if 'login' in raw.lower() and ('register' in raw.lower() or 'kc-form' in raw.lower() or 'sign' in raw.lower()):
    print('  page 含注册表单元件?', flush=True)
m = re.search(r'<title>([^<]*)</title>', raw)
print('  title:', m.group(1) if m else 'N/A', flush=True)
for kw in ['register', 'create account', 'sign up', 'not allowed', 'challenge', 'cloudflare', 'cf-']:
    if kw in raw.lower():
        print('  含关键词:', kw, flush=True)

print('\n=== 2. openid-configuration ===', flush=True)
st, raw, hdrs = get('console.neon.tech', '/realms/prod-realm/.well-known/openid-configuration')
print('->', st, flush=True)
if st == 200:
    import json
    try:
        d = json.loads(raw)
        for k in ['registration_endpoint', 'authorization_endpoint', 'issuer']:
            print(' ', k, '=', d.get(k), flush=True)
    except Exception as e:
        print('  parse err', e, flush=True)
        print(raw[:400], flush=True)

print('\n=== 3. console 注册页 ===', flush=True)
for p in ['/register', '/signup', '/auth/register', '/sign-up']:
    st, raw, hdrs = get('console.neon.tech', p)
    loc = hdrs.get('location', '')
    print('[%s] -> %d loc=%s len=%d' % (p, st, loc[:100], len(raw)), flush=True)

print('\n=== 4. console 注册 API ===', flush=True)
# Neon console 注册可能走 /api/register 或 keycloak; 看主登录页跳转链
st, raw, hdrs = get('console.neon.tech', '/login')
loc = hdrs.get('location', '')
print('[/login] -> %d loc=%s' % (st, loc[:150]), flush=True)
