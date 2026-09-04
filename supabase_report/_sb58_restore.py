# -*- coding: utf-8 -*-
"""还原: ssl-enforcement false + jit-access disabled (恢复测试前状态)"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag=''):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + BEARER_JWT}
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(4000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:1500]))
        c.close()
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))

# 1. ssl-enforcement 还原 false
req('PUT', '/v1/projects/%s/ssl-enforcement' % PROJECT_REF, {"requestedConfig": {"database": False}}, 'ssl-off')
time.sleep(2)
req('GET', '/v1/projects/%s/ssl-enforcement' % PROJECT_REF, None, 'ssl-verify')
# 2. jit-access 关闭
req('PUT', '/v1/projects/%s/jit-access' % PROJECT_REF, {"state": "disabled"}, 'jit-off')
time.sleep(1)
req('GET', '/v1/projects/%s/jit-access' % PROJECT_REF, None, 'jit-verify')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb58_restore.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
