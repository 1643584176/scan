# -*- coding: utf-8 -*-
"""自测:账号 A 对自己资源的正确路径与返回形态"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(token, path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=20)
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

# 1. accounts 完整(id 字段)
st, raw = api(TOKEN_A, '/api/v1/accounts')
accts = json.loads(raw) if st == 200 else []
print('A accounts:')
for a in accts:
    print('  id=%s slug=%s name=%s' % (a.get('id'), a.get('slug'), a.get('name')))
acc_a = accts[0].get('id') if accts else None
print()

# 2. A 对自己的资源(路径有效性确认)
tests = [
    ('A site env',            '/api/v1/sites/%s/env' % SITE_A),
    ('A site env?context',    '/api/v1/sites/%s/env?scope=any' % SITE_A),
    ('A account env',         '/api/v1/accounts/%s/env' % acc_a if acc_a else 'SKIP'),
    ('A metadata',            '/api/v1/sites/%s/metadata' % SITE_A),
    ('A site db owner',       '/api/v1/sites/%s/database?role=netlifydb_owner' % SITE_A),
    ('A site db branches',    '/api/v1/sites/%s/database/branches' % SITE_A),
    ('A deploys',             '/api/v1/sites/%s/deploys?per_page=3' % SITE_A),
    ('A functions list',      '/api/v1/sites/%s/functions' % SITE_A),
]
for label, p in tests:
    if p == 'SKIP':
        print('%-24s SKIP' % label)
        continue
    st, raw = api(TOKEN_A, p)
    print('%-24s %s %s' % (label, st, raw[:200].decode('utf-8', 'replace').replace('\n', ' ')))
