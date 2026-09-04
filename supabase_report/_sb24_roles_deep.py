# -*- coding: utf-8 -*-
"""角色深盘: postgres 行属性/内部角色/成员关系/SET ROLE 边界 (事务级零副作用)"""
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
        b = r.read(6000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:3000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. 全角色名+关键属性 (只输出名字列避免截断, 再单独看关键角色)
q("select rolname, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolcanlogin, rolinherit from pg_roles order by 1;", "all-roles")
# 2. 内部角色是否存在 + 属性
q("select rolname, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolcanlogin from pg_roles where rolname in ('postgres','supabase_admin','service_role','supabase_read_only_user','supabase_storage_admin','supabase_auth_admin','dashboard_user','authenticator','anon','authenticated');", "key-roles")
# 3. postgres 的成员关系 (postgres 在哪些角色里)
q("select r.rolname member_of from pg_roles r join pg_auth_members m on m.roleid = r.oid join pg_roles me on me.oid = m.member where me.rolname='postgres';", "pg-memberships")
# 4. 谁能 SET ROLE 到内部角色 (直接成员+继承)
q("select rolname from pg_roles where rolname in ('supabase_admin','service_role','dashboard_user','supabase_read_only_user','supabase_storage_admin','supabase_auth_admin','authenticator') and (pg_has_role(current_user, oid, 'MEMBER'));", "can-setrole")
# 5. 事务级 set role 试探 (自动回滚, 零副作用) - 每个角色独立事务
for rname in ['supabase_admin', 'dashboard_user', 'service_role', 'supabase_read_only_user', 'authenticator']:
    q("begin; set local role %s; select current_user, current_setting('is_superuser'); rollback;" % rname, 'try-role-' + rname)
# 6. pg_authid 为什么能读 - 查 ACL
q("select relname, relacl from pg_class where relname in ('pg_authid','pg_roles');", "authid-acl")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb24_deep.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:8000])
