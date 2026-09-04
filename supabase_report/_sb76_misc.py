# -*- coding: utf-8 -*-
"""末批探针: pg_graphql introspection + admin generate_link token 面 + pgrst plan header"""
import http.client, ssl, json, time, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import VDP_HEADERS, UA, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = '%s.supabase.co' % PROJECT_REF
ctx = ssl.create_default_context()
out = []
def call(method, path, body=None, tag='', bearer=None, apikey=ANON_KEY, maxb=10000, retries=2, extra_h=None):
    body_j = json.dumps(body) if body is not None else None
    for i in range(retries):
        c = http.client.HTTPSConnection(HOST, timeout=25, context=ctx)
        h = {"User-Agent": UA, "Accept": "application/json", "apikey": apikey,
             "Authorization": "Bearer " + (bearer or apikey)}
        if body_j:
            h["Content-Type"] = "application/json"
        if extra_h:
            h.update(extra_h)
        h.update(VDP_HEADERS)
        t0 = time.time()
        try:
            c.request(method, path, headers=h, body=body_j)
            r = c.getresponse()
            b = r.read(maxb).decode('utf-8', errors='replace')
            out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2000]))
            c.close()
            return r.status, b
        except Exception as e:
            out.append('### [%s] %s %s try%d ERR %s' % (tag, method, path, i + 1, e))
            time.sleep(1.5)
    return 0, ''

# 1. pg_graphql 端点活跃性 (anon)
call('POST', '/graphql/v1', {"query": "{ __schema { queryType { name } } }"}, 'gql-anon')
# 2. pg_graphql service_role
call('POST', '/graphql/v1', {"query": "{ __schema { queryType { name } } }"}, 'gql-sr', apikey=SR_KEY)
# 3. generate_link recovery (sr) - token 格式/长度
st, b = call('POST', '/auth/v1/admin/generate_link', {"type": "recovery", "email": "sbx_auvjijfz@qq.com"},
             'gen-link-recovery', apikey=SR_KEY)
# 4. generate_link invite (sr) - 项目里未配置 invite?
st2, b2 = call('POST', '/auth/v1/admin/generate_link', {"type": "invite", "email": "sbx_nobody_x1@qq.com"},
               'gen-link-invite', apikey=SR_KEY)
# 5. PostgREST plan header (anon) - 拒绝?
call('GET', '/rest/v1/sbx_rls_t?select=id', 'pgrst-plan-anon', extra_h={"Prefer": "plan=count"})
# 6. PostgREST server-timing / 深度 header 枚举 (anon)
call('OPTIONS', '/rest/v1/sbx_rls_t', None, 'pgrst-options')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb76_misc.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
