# -*- coding: utf-8 -*-
"""Netlify 写面交叉验证:B token 对 A 资源的写操作(期待 401/404;若 200 记录并撤销)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ACC_ID_A = '6a979dd2ae93f47d55b62897'
ctx = ssl.create_default_context()

def api(token, path, method='GET', body=None, raw_body=None, ctype='application/json'):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Authorization': 'Bearer ' + token, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
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
        return 'ERR', str(e)[:60].encode()

writes = [
    # (label, method, path, body)
    ('B create build_hook on A', 'POST', '/api/v1/sites/%s/build_hooks' % SITE_A, {'title': 'x-probe', 'branch': 'main'}),
    ('B create snippet on A',    'POST', '/api/v1/sites/%s/snippets' % SITE_A, {'title': 'x-probe', 'general': '<script>1</script>'}),
    ('B create hook on A',       'POST', '/api/v1/hooks?site_id=%s' % SITE_A, {'type': 'email', 'event': 'deploy_created', 'data': {}}),
    ('B create dns zone',        'POST', '/api/v1/dns_zones', {'name': 'x-probe-%d.example.com' % __import__('random').randint(1000, 9999), 'account_slug': '1643584176'}),
    ('B purge A site',           'POST', '/api/v1/purge', {'site_id': SITE_A}),
    ('B add member to A',        'POST', '/api/v1/1643584176/members', {'email': 'nobody-x@example.com', 'role': 'Designer'}),
    ('B list A members',         'GET',  '/api/v1/1643584176/members', None),
    ('B list A sites',           'GET',  '/api/v1/1643584176/sites', None),
    ('B PATCH A site',           'PATCH', '/api/v1/sites/%s' % SITE_A, {'name': 'x-probe-renamed'}),
    ('B create account env',     'POST', '/api/v1/accounts/%s/env' % ACC_ID_A, {'env_vars': [{'key': 'X_PROBE', 'values': [{'context': 'production', 'value': '1'}]}]}),
]
for label, m, p, b in writes:
    st, raw = api(TOKEN_B, p, m, b)
    print('%-28s %s %s' % (label, st, raw[:200].decode('utf-8', 'replace').replace('\n', ' ')))
