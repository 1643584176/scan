# -*- coding: utf-8 -*-
"""authorize-no-rhost 响应补看 + 清理 postgres 映射还原状态"""
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
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

# 1. 无 rhost authorize 完整响应
req('POST', '/v1/projects/%s/database/jit' % PROJECT_REF, {"role": "postgres"}, 'no-rhost-2')
# 2. 清理: 映射清空 (还原 PUT 前状态)
req('PUT', '/v1/projects/%s/database/jit' % PROJECT_REF,
    {"user_id": "68ef6708-65ba-4411-82fb-ea59015a04e9", "roles": []}, 'clean-map')
# 3. 确认还原
req('GET', '/v1/projects/%s/database/jit' % PROJECT_REF, None, 'verify-clean')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb57_clean.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
