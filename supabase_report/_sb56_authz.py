# -*- coding: utf-8 -*-
"""映射就绪后 authorize 重测 + 若成功则尝试 JIT 凭据面"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', maxb=8000):
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
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:3000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

# 1. 映射(postgres)就绪后 authorize
st, b = req('POST', '/v1/projects/%s/database/jit' % PROJECT_REF, {"role": "postgres", "rhost": "1.1.1.1"}, 'authorize-2')
# 2. authorize 变体: 无 rhost / role 不匹配 / 不同 rhost
req('POST', '/v1/projects/%s/database/jit' % PROJECT_REF, {"role": "postgres", "rhost": "8.8.8.8"}, 'authorize-ip2')
req('POST', '/v1/projects/%s/database/jit' % PROJECT_REF, {"role": "supabase_read_only_user", "rhost": "1.1.1.1"}, 'authorize-other-role')
req('POST', '/v1/projects/%s/database/jit' % PROJECT_REF, {"role": "postgres"}, 'authorize-no-rhost')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb56_authz.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
