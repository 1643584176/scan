# -*- coding: utf-8 -*-
"""authorize JIT 端点 gate 层探测 (功能关闭态行为) + 路径清单输出"""
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
        return r.status
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0

# 1. authorize: 功能关闭态行为 (role 用不存在的测试名避免副作用)
req('POST', '/v1/projects/%s/database/jit' % PROJECT_REF, {"role": "sbx_nonexistent_role_probe", "rhost": "1.1.1.1"}, 'jit-authorize-off')
# 2. PUT update: 功能关闭态行为 (改自己的 user_id 映射 -- 若意外成功会记录, 需清理)
import uuid
req('PUT', '/v1/projects/%s/database/jit' % PROJECT_REF, {"user_id": "68ef6708-65ba-4411-82fb-ea59015a04e9", "roles": [{"role": "sbx_nonexistent_role_probe", "expires_at": 1788511000}]}, 'jit-update-off')
# 3. DELETE 面 (若 PUT 成功则清掉)
req('DELETE', '/v1/projects/%s/database/jit' % PROJECT_REF, {"user_id": "68ef6708-65ba-4411-82fb-ea59015a04e9"}, 'jit-delete-off')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb35_jitgate.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out))
