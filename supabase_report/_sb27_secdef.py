# -*- coding: utf-8 -*-
"""SECURITY DEFINER 函数/触发器/平台对象 owner 扫描 + 扩展安装边界 (可逆)"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

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
        b = r.read(10000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:6000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. SECURITY DEFINER 函数 (平台 schema, owner 列)
q("select p.proname, n.nspname, p.proowner::regrole as owner, p.prosecdef, p.prosecdefwc from pg_proc p join pg_namespace n on n.oid=p.pronamespace where p.prosecdef and n.nspname in ('auth','storage','extensions','vault','realtime','graphql','graphql_public','public','pgbouncer') order by n.nspname, p.proname limit 200;", "secdef-funcs")
# 2. 平台 schema 表 owner (auth/storage/vault/realtime/extensions)
q("select c.relname, n.nspname, c.relowner::regrole as owner, c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('auth','storage','vault','realtime','extensions','graphql','pgbouncer') and c.relkind in ('r','v') order by n.nspname, c.relname limit 200;", "plat-tables")
# 3. 非 internal 触发器
q("select t.tgname, c.relname, n.nspname, t.tgfoid::regproc as fn from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace where not t.tgisinternal and n.nspname in ('auth','storage','extensions','vault','realtime','public') order by 1;", "triggers")
# 4. 扩展安装边界: postgres_fdw (SupaPwn 组件)
q("create extension if not exists postgres_fdw;", "ext-fdw")
q("select extname, extversion from pg_extension where extname='postgres_fdw';", "chk-fdw")
q("create server if not exists sbx_fdw_srv foreign data wrapper postgres_fdw options (host '127.0.0.1', port '5432', dbname 'postgres');", "fdw-server")
q("drop server if exists sbx_fdw_srv;", "clean-srv")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb27_secdef.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:8000])
