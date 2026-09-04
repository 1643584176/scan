# -*- coding: utf-8 -*-
"""invite 矩阵: 角色/邮箱/参数变体区分 500 原因"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(tag, body):
    body_j = json.dumps(body)
    c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/jit/invite' % PROJECT_REF, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(4000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:1200]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

FUT = int(time.time()) + 3600
# 1. 存在但低权限角色 + 自己邮箱
req('rol-ro', {"email": "1643584176@qq.com", "roles": [{"role": "supabase_read_only_user", "expires_at": FUT}]})
# 2. 不存在的邮箱 (用户存在性校验?)
req('nouser', {"email": "sbx_nonexistent_9x7k@example.com", "roles": [{"role": "postgres", "expires_at": FUT}]})
# 3. anon 角色 (公开角色, 非特权)
req('rol-anon', {"email": "sbx_other_9x7k@qq.com", "roles": [{"role": "anon", "expires_at": FUT}]})
# 4. 带 allowed_networks (完整参数形态)
req('full', {"email": "1643584176@qq.com",
             "roles": [{"role": "postgres", "expires_at": FUT,
                        "allowed_networks": {"allowed_cidrs": [{"cidr": "1.1.1.1/32"}]}}]})
# 5. 无 expires_at (纯 role)
req('norole-exp', {"email": "1643584176@qq.com", "roles": [{"role": "postgres"}]})

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb51_invmat.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
