# -*- coding: utf-8 -*-
"""残留清理: 扩展 (pg_net/pg_cron/postgres_fdw/file_fdw) + FDW server + 自建角色"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def q(sql, tag):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(8000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:3000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. 残留盘点
q("select extname from pg_extension where extname in ('pg_net','pg_cron','postgres_fdw','file_fdw','dblink');", 'ext-list')
q("select srvname from pg_foreign_server;", 'srv-list')
q("select rolname from pg_roles where rolname like 'sbx%' or rolname like 'cli_%';", 'role-list')
q("select schemaname, tablename from pg_tables where schemaname='public' and tablename like 'sbx%';", 'tbl-list')
# 2. 清理 FDW server (若有)
q("do $$ declare s record; begin for s in select srvname from pg_foreign_server loop execute format('drop server if exists %I cascade', s.srvname); end loop; end $$;", 'drop-srv')
# 3. drop 扩展
q("drop extension if exists pg_net cascade; drop extension if exists pg_cron cascade; drop extension if exists dblink cascade;", 'drop-ext')
# 4. drop 自建角色
q("do $$ declare r record; begin for r in select rolname from pg_roles where rolname like 'sbx%' loop execute format('drop role if exists %I', r.rolname); end loop; end $$;", 'drop-roles')
# 5. 复查
q("select extname from pg_extension where extname in ('pg_net','pg_cron','postgres_fdw','file_fdw','dblink');", 'ext-recheck')
q("select srvname from pg_foreign_server;", 'srv-recheck')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb59_cleanup.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
