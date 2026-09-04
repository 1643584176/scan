# -*- coding: utf-8 -*-
"""signing-keys + pooler + context 探测 (密钥面影响评估)"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, tag='', maxb=10000):
    c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:6000]))
        c.close()
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))

req('GET', '/v1/projects/%s/config/auth/signing-keys' % PROJECT_REF, 'signing-keys')
req('GET', '/v1/projects/%s/config/auth/signing-keys/legacy' % PROJECT_REF, 'signing-legacy')
req('GET', '/v1/projects/%s/config/database/pooler' % PROJECT_REF, 'pooler')
req('GET', '/v1/projects/%s/database/context' % PROJECT_REF, 'db-ctx')
req('GET', '/v1/projects/%s/readonly' % PROJECT_REF, 'readonly')
req('GET', '/v1/projects/%s/config/database/pgbouncer' % PROJECT_REF, 'pgbouncer-cfg')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb46_keys.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:9000])
