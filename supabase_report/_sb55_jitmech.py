# -*- coding: utf-8 -*-
"""JIT enabled 后机制深测: authorize + PUT postgres 映射 + DB 层对象变化"""
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
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2500]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

def q(sql, tag, maxb=20000):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:16000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

MY_IP = '1.1.1.1'  # 任意合法 rhost (记录用)
# 1. authorize (JIT enabled 后; 自己的映射为空)
req('POST', '/v1/projects/%s/database/jit' % PROJECT_REF, {"role": "postgres", "rhost": MY_IP}, 'authorize-pg')
# 2. PUT 给自己真实角色 postgres + expires 1h (可逆: 之后清空)
FUT = int(time.time()) + 3600
req('PUT', '/v1/projects/%s/database/jit' % PROJECT_REF,
    {"user_id": "68ef6708-65ba-4411-82fb-ea59015a04e9",
     "roles": [{"role": "postgres", "expires_at": FUT}]}, 'put-postgres')
# 3. GET 自己映射确认
req('GET', '/v1/projects/%s/database/jit' % PROJECT_REF, None, 'get-self')
# 4. DB 层变化: JIT 相关新角色/表 (enabled 后平台可能建了对象)
q("select rolname, rolsuper, rolcanlogin, rolvaliduntil from pg_roles where rolname ilike '%jit%' or rolname ilike '%auth%' order by 1;", "db-roles-jit")
q("select n.nspname, c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema','pg_toast') and (c.relname ilike '%jit%' or c.relname ilike '%authz%') order by 1,2;", "db-objs-jit")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb55_jitmech.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
