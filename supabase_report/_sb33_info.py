# -*- coding: utf-8 -*-
"""只读信息探针: JIT 映射现状 + api-keys 结构 + claim-token 状态"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', maxb=6000):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + BEARER_JWT}
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

# 1. JIT user-id -> role mappings (读)
req('GET', '/v1/projects/%s/database/jit' % PROJECT_REF, None, 'jit-mappings')
# 2. api-keys 列表 (结构; 避免输出完整 secret, 截断显示)
req('GET', '/v1/projects/%s/api-keys' % PROJECT_REF, None, 'api-keys', maxb=12000)
# 3. claim-token 状态
req('GET', '/v1/projects/%s/claim-token' % PROJECT_REF, None, 'claim-state')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb33_info.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:6000])
