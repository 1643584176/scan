# -*- coding: utf-8 -*-
"""数据面服务测试: public 表权限图 + auth.users + anon/service_role 服务探测"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDM2MjQsImV4cCI6MjEwNDA3OTYyNH0.DNQluKwykRJKoIRtWRd5AJCZTysTZEEGc3ooMZ6B_7Q"
SR_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZm9iYnl3ZW1xZ2Nnam9ra3hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODUwMzYyNCwiZXhwIjoyMTA0MDc5NjI0fQ.Uq8457YU68HS3Xw9LFRyQIGQfxSNy9jXcVKdkKuucvE"
HOST = "vnfobbywemqgcgjokkxd.supabase.co"
DB_HOST = "db.vnfobbywemqgcgjokkxd.supabase.co"

ctx = ssl.create_default_context()
out = []

def q(sql, tag):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(20000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:12000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

def svc(method, path, tag, key=None, body=None, host=HOST):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(host, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "apikey": key or ANON_KEY,
         "Authorization": "Bearer " + (key or ANON_KEY)}
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

# 1. public schema 表权限图 (anon/authenticated/service_role 视角 + RLS)
q("""select c.relname, c.relkind, c.relrowsecurity rls,
  has_table_privilege('anon', c.oid, 'SELECT') anon_sel,
  has_table_privilege('authenticated', c.oid, 'SELECT') auth_sel,
  has_table_privilege('service_role', c.oid, 'SELECT') sr_sel,
  (select count(*) from pg_policy p where p.polrelid=c.oid) pols
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relkind in ('r','p','v','f','m')
order by c.relname;""", "pub-perms")
# 2. auth.users / storage.objects 行数 (postgres 通道可读性)
q("select (select count(*) from auth.users) au, (select count(*) from storage.objects) so, (select count(*) from auth.identities) ai;", "svc-counts")
# 3. anon key: PostgREST 根 + 枚举
svc('GET', '/rest/v1/', 'pgrst-anon')
# 4. service_role: PostgREST 根
svc('GET', '/rest/v1/', 'pgrst-sr', key=SR_KEY)
# 5. service_role: GoTrue admin users (脱敏? 只取 per_page=2)
svc('GET', '/auth/v1/admin/users?per_page=2', 'gotrue-admin', key=SR_KEY)
# 6. service_role: Storage buckets
svc('GET', '/storage/v1/bucket', 'storage-sr', key=SR_KEY)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb34_svc.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:7000])
