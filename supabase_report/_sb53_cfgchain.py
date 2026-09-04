# -*- coding: utf-8 -*-
"""配置链: ssl-enforcement enable -> jit-access enable -> invite 重试 (全部记录, 后续还原)"""
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
        b = r.read(6000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

# 1. 当前状态
req('GET', '/v1/projects/%s/ssl-enforcement' % PROJECT_REF, None, 'ssl-before')
req('GET', '/v1/projects/%s/jit-access' % PROJECT_REF, None, 'jit-before')
# 2. 开 ssl-enforcement (spec 正确 body)
req('PUT', '/v1/projects/%s/ssl-enforcement' % PROJECT_REF, {"requestedConfig": {"database": True}}, 'ssl-enable')
time.sleep(2)
req('GET', '/v1/projects/%s/ssl-enforcement' % PROJECT_REF, None, 'ssl-after')
# 3. 开 JIT
req('PUT', '/v1/projects/%s/jit-access' % PROJECT_REF, {"state": "enabled"}, 'jit-enable')
time.sleep(1)
req('GET', '/v1/projects/%s/jit-access' % PROJECT_REF, None, 'jit-after')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb53_cfgchain.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
