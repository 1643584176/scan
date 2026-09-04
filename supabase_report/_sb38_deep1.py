# -*- coding: utf-8 -*-
"""DB 细测 A: 平台 SQL 情报 + pg_authid ACL 机制 + vault/pgsodium 密钥可读性 + migrations"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def q(sql, tag, maxb=20000):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:12000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. 平台关键设置 (preload 库 => hook 痕迹)
q("select name, setting, source from pg_settings where name in ('shared_preload_libraries','session_preload_libraries','dynamic_library_path','data_directory','password_encryption','log_statement','log_min_duration_statement','ssl','huge_pages') order by 1;", "settings")
# 2. pg_authid ACL 机制: owner + relacl + postgres 直查权限
q("select c.relname, a.rolname owner, c.relacl from pg_class c join pg_namespace n on n.oid=c.relnamespace join pg_authid a on a.oid=c.relowner where n.nspname='pg_catalog' and c.relname in ('pg_authid','pg_roles','pg_shadow','pg_user');", "authid-acl")
# 3. 完整读一个 rolpassword (supabase_read_only_user 的哈希 -- 自己的只读角色, 无敏感) 确认无脱敏
q("select rolname, rolpassword from pg_authid where rolname='supabase_read_only_user';", "authid-full")
# 4. pg_stat_statements 可读性 (平台服务 SQL 情报)
q("select count(*) n, min(calls) mc from pg_stat_statements;", "pss-count")
# 5. auth/storage schema_migrations 版本情报
q("select 'auth' src, version from auth.schema_migrations order by id desc limit 3;", "auth-migr")
q("select 'storage' src, version from storage.schema_migrations order by id desc limit 3;", "stor-migr")
# 6. pgsodium.key 可读性 (vault 主密钥是否在库内可见)
q("select id, name, status, key_type, length(decrypted_key) keylen from pgsodium.key;", "pgsodium-keys")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb38_deep1.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:7500])
