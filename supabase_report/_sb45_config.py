# -*- coding: utf-8 -*-
"""spec v1 Database/Config tag 端点清单 + config GET 探测"""
import json, os, http.client, ssl, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

d = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(d, '_sb16_openapi.json'), encoding='utf-8'))

out = []
# 1. Database tag 路径清单
for p in sorted(spec['paths']):
    if p.startswith('/v1/projects/{ref}/'):
        ops = spec['paths'][p]
        for m in ['get', 'post', 'put', 'patch', 'delete']:
            if m in ops:
                tags = ops[m].get('tags', [])
                if any(t in ('Database', 'Auth', 'Edge Functions', 'Storage') for t in tags):
                    out.append('%s %s tags=%s fga=%s' % (m.upper(), p, tags,
                        ops[m].get('x-fga-permissions', '')))
out.append('=== paths above ===')

ctx = ssl.create_default_context()
def req(method, path, tag=''):
    c = http.client.HTTPSConnection(API_HOST, timeout=15, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h)
        r = c.getresponse()
        b = r.read(6000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2000]))
        c.close()
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))

# 2. config 读探测 (哪些含敏感)
req('GET', '/v1/projects/%s/config/auth' % PROJECT_REF, 'cfg-auth')
req('GET', '/v1/projects/%s/config/database' % PROJECT_REF, 'cfg-db')
req('GET', '/v1/projects/%s/config/database/postgres' % PROJECT_REF, 'cfg-db-pg')
req('GET', '/v1/projects/%s/config/network-restrictions' % PROJECT_REF, 'cfg-net')
req('GET', '/v1/projects/%s/config/storage' % PROJECT_REF, 'cfg-storage')
req('GET', '/v1/projects/%s/database/backups' % PROJECT_REF, 'db-backups')
req('GET', '/v1/projects/%s/database/status' % PROJECT_REF, 'db-status')

open(os.path.join(d, '_sb45_config.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:9000])
