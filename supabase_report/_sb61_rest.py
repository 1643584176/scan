# -*- coding: utf-8 -*-
"""剩余信息面扫描: sso/third-party/storage/functions/backups/openapi/types"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, tag='', maxb=6000):
    c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] %s (%.1fs)\n%s | %s' % (tag, path, time.time() - t0, r.status, b[:1500]))
        c.close()
    except Exception as e:
        out.append('### [%s] %s ERR %s' % (tag, path, e))

P = '/v1/projects/%s' % PROJECT_REF
req('GET', P + '/config/auth/sso/providers', 'sso')
req('GET', P + '/config/auth/third-party-auth', 'tpa')
req('GET', P + '/config/storage', 'stor-cfg')
req('GET', P + '/functions', 'funcs')
req('GET', P + '/database/backups', 'backups')
req('GET', P + '/database/openapi', 'db-openapi', maxb=2000)
req('GET', P + '/types/typescript', 'ts-types', maxb=2000)
req('GET', '/v1/profile', 'profile')
req('GET', '/v1/organizations', 'orgs')
req('GET', '/v1/projects', 'projects')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb61_rest.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
