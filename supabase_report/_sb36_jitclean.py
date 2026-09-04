# -*- coding: utf-8 -*-
"""验证 PUT 持久化 + 清理映射脏数据"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag=''):
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
        b = r.read(4000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:1500]))
        c.close()
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))

# 1. GET 复查 (映射是否持久化)
req('GET', '/v1/projects/%s/database/jit' % PROJECT_REF, None, 'jit-get-again')
# 2. 清理: PUT 空 roles
req('PUT', '/v1/projects/%s/database/jit' % PROJECT_REF, {"user_id": "68ef6708-65ba-4411-82fb-ea59015a04e9", "roles": []}, 'jit-clean-1')
# 3. 清理复查
req('GET', '/v1/projects/%s/database/jit' % PROJECT_REF, None, 'jit-get-after-clean')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb36_jitclean.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out))
