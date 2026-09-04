# -*- coding: utf-8 -*-
"""Netlify:尝试无 repo 触发构建(zip 构建),探测构建面"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def api(token, path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Authorization': 'Bearer ' + token}
    payload = None
    if body is not None:
        h['Content-Type'] = 'application/json'
        payload = json.dumps(body).encode()
    try:
        conn.request(method, path, body=payload, headers=h)
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st = r.status
        conn.close()
        return st, raw
    except Exception as e:
        return 'ERR', str(e)[:80].encode()

# 1. site 详情(build_settings / repo 状态)
st, raw = api(TOKEN_B, '/api/v1/sites/%s' % SITE_B)
if st == 200:
    s = json.loads(raw)
    print('site: name=%s repo=%s' % (s.get('name'), s.get('build_settings', {}).get('repo_url')))
    print('  build_image=%s cmd=%s dir=%s' % (
        s.get('build_settings', {}).get('build_image'),
        s.get('build_settings', {}).get('cmd'),
        s.get('build_settings', {}).get('dir')))
else:
    print('site ERR', st, raw[:200])
print()

# 2. 尝试触发构建(多种 body)
tests = [
    ('zip=true',     {'zip': True}),
    ('zip+branch',   {'zip': True, 'branch': 'main'}),
    ('plain',        {}),
    ('branch only',  {'branch': 'main'}),
]
for label, b in tests:
    st, raw = api(TOKEN_B, '/api/v1/sites/%s/builds' % SITE_B, 'POST', b)
    print('%-14s %s %s' % (label, st, raw[:300].decode('utf-8', 'replace').replace('\n', ' ')))

# 3. 现有 builds 列表(如果有)
st, raw = api(TOKEN_B, '/api/v1/sites/%s/builds' % SITE_B)
print('builds list:', st, raw[:300].decode('utf-8', 'replace').replace('\n', ' '))
