# -*- coding: utf-8 -*-
"""DB 细测 B: pg_stat_statements 平台 SQL dump + auth migrations + vault 结构 + pg_net 扩展边界"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

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
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:24000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. pg_stat_statements: 按 calls 高频 (平台服务 SQL -- 排除已知自身查询特征困难, 看全貌)
q("select calls, round(mean_exec_time::numeric,1) ms, round(total_exec_time::numeric/1000,1) ts, left(query, 400) q from pg_stat_statements order by calls desc limit 30;", "pss-top-calls")
# 2. pg_stat_statements: 含 auth. 平台操作的语句 (GoTrue/mgmt 痕迹)
q("select calls, left(query, 400) q from pg_stat_statements where query ilike '%auth.%' or query ilike '%pg_authid%' or query ilike '%realtime%' or query ilike '%supabase_admin%' order by calls desc limit 20;", "pss-platform")
# 3. auth.schema_migrations 修正 (查结构先)
q("select column_name, data_type from information_schema.columns where table_schema='auth' and table_name='schema_migrations';", "auth-migr-cols")
# 4. vault schema 全对象 (0.3.1 密钥管理机制)
q("select c.relname, c.relkind, c.relowner::regrole from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='vault' order by c.relkind, c.relname;", "vault-objs")
# 5. pg_net 扩展创建边界 (preload 已加载; create extension 需 superuser 吗)
q("create extension if not exists pg_net;", "ext-pgnet")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb39_deep2.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:9500])
