# -*- coding: utf-8 -*-
"""平台连接面 + JIT 启用链: pg_stat_activity 拓扑 + ssl-enforcement/JIT 状态机"""
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
        b = r.read(5000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:1600]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

def q(sql, tag):
    return req('POST', '/v1/projects/%s/database/query' % PROJECT_REF, {"query": sql}, tag)

# 1. pg_stat_activity: 平台连接角色/IP/应用名
q("select usename, application_name, client_addr, state, backend_type from pg_stat_activity where backend_type='client backend' order by usename;", 'activity')
# 2. JIT 状态 + ssl-enforcement 当前状态
req('GET', '/v1/projects/%s/jit-access' % PROJECT_REF, None, 'jit-state')
req('GET', '/v1/projects/%s/ssl-enforcement' % PROJECT_REF, None, 'ssl-state')
# 3. 试 enable JIT (预期被拒: ssl)
req('PUT', '/v1/projects/%s/jit-access' % PROJECT_REF, {"state": "enabled"}, 'jit-enable')
# 4. 试 enable ssl (零破坏? 改配置, 可逆; body 按 spec 猜 {"enabled": true})
req('PUT', '/v1/projects/%s/ssl-enforcement' % PROJECT_REF, {"enabled": True}, 'ssl-enable')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb31_jit.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:7000])
