# -*- coding: utf-8 -*-
"""X-CSRF-Token header 认证测试: cookie + X-CSRF-Token=_gorilla_csrf raw value"""
import http.client, ssl, json, sys, os, re

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import COOKIE_RAW, API_HOST

m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)
print('csrf raw len:', len(CSRF), flush=True)

def req(path, csrf=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Cookie': COOKIE_RAW, 'X-CSRF-Token': csrf or ''}
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw[:500].replace('\n', ' ')
    except Exception as e:
        return -1, 'EXC %s' % e

for p in ['/api/v2/projects', '/api/v2/users/me', '/api/v2/database_instances',
          '/api/v2/organizations', '/api/v2/resolve-lakebase-regions']:
    st, body = req(p, CSRF)
    print('%-45s %s %s' % (p, st, body[:220]), flush=True)
