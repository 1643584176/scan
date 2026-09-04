# -*- coding: utf-8 -*-
"""Management API 控制面: cli/login-role 角色权限审计 + claim-token 格式 (创建后清理)"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag=''):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + BEARER_JWT}
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(4000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:1200]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

def q(sql, tag):
    return req('POST', '/v1/projects/%s/database/query' % PROJECT_REF, {"query": sql}, tag)

# 1. CLI login-role 创建 (read_only: false)
st, b = req('POST', '/v1/projects/%s/cli/login-role' % PROJECT_REF, {"read_only": False}, 'login-role-rw')
# 2. 查询新角色属性 (名字模式猜: cli_* 或 supabase_cli_*)
q("select rolname, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolcanlogin, rolvaliduntil from pg_roles where rolname ilike '%cli%' or rolname ilike 'sbx%' or rolname like 'pg_temp%' order by 1;", 'chk-cli-role')
# 3. 成员关系
q("select r.rolname role, me.rolname member, m.admin_option from pg_auth_members m join pg_roles r on r.oid=m.roleid join pg_roles me on me.oid=m.member where r.rolname ilike '%cli%' or me.rolname ilike '%cli%' or r.rolname like 'sbx%' or me.rolname like 'sbx%';", 'chk-cli-member')
# 4. 清理 CLI 角色
req('DELETE', '/v1/projects/%s/cli/login-role' % PROJECT_REF, None, 'del-login-role')
# 5. claim-token 创建 + 查询
req('POST', '/v1/projects/%s/claim-token' % PROJECT_REF, None, 'mk-claim')
req('GET', '/v1/projects/%s/claim-token' % PROJECT_REF, None, 'get-claim')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb30_mgmt.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:8000])
