# -*- coding: utf-8 -*-
"""JIT invite 链实测: list + invite 自己邮箱 (探测校验逻辑) + 若成功则 accept 尝试 + 清理"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF, EMAIL

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
        b = r.read(6000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2500]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

# 1. 全量映射列表 (owner 视角)
st, b = req('GET', '/v1/projects/%s/database/jit/list' % PROJECT_REF, None, 'jit-list')
# 2. invite 自己主邮箱 + role postgres (若自邀被拒 => 服务端有校验)
st, b = req('POST', '/v1/projects/%s/database/jit/invite' % PROJECT_REF,
            {"email": EMAIL, "roles": [{"role": "postgres"}]}, 'jit-invite-self')
# 3. 若 invite 成功 (200 含 invite_id), 试 accept (body 猜测: {invite_id} / {token} / {email, token})
if st == 200 and 'invite_id' in b:
    try:
        inv = json.loads(b)
        iid = inv.get('invite_id') or (inv.get('items') or [{}])[0].get('invite_id')
        if iid:
            req('POST', '/v1/projects/%s/database/jit/invite/accept' % PROJECT_REF,
                {"invite_id": iid}, 'jit-accept-iid')
            req('POST', '/v1/projects/%s/database/jit/invite/accept' % PROJECT_REF,
                {"email": EMAIL, "invite_id": iid}, 'jit-accept-email')
            # 清理
            req('DELETE', '/v1/projects/%s/database/jit/invite/%s' % (PROJECT_REF, iid), None, 'jit-del-invite')
    except Exception as e:
        out.append('### parse ERR %s' % e)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb49_invite.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
