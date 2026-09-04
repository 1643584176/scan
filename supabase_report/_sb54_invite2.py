# -*- coding: utf-8 -*-
"""JIT enabled 后: invite 重试 (自己邮箱) + list 状态"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF, EMAIL

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
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2500]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

FUT = int(time.time()) + 3600
# 1. invite 自己主邮箱 + postgres (JIT enabled 后)
st, b = req('POST', '/v1/projects/%s/database/jit/invite' % PROJECT_REF,
            {"email": EMAIL, "roles": [{"role": "postgres", "expires_at": FUT}]}, 'invite-1')
# 2. invite 另一邮箱 (测试是否允许邀请任意地址)
st2, b2 = req('POST', '/v1/projects/%s/database/jit/invite' % PROJECT_REF,
              {"email": "sbx_victim_9x7k@qq.com", "roles": [{"role": "postgres", "expires_at": FUT}]}, 'invite-2')
# 3. list 看状态
req('GET', '/v1/projects/%s/database/jit/list' % PROJECT_REF, None, 'jit-list')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb54_invite2.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
