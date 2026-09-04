# -*- coding: utf-8 -*-
"""DB 细测 E: auth 表 ACL 面 (anon/authenticated 可读?) + read_only 通道 pg_authid 读测 + cron 面"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def q(sql, tag, read_only=None, maxb=30000):
    body = {"query": sql}
    if read_only is not None:
        body["read_only"] = read_only
    bj = json.dumps(body)
    c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=bj)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] ro=%s (%.1fs)\n%s | %s' % (tag, read_only, time.time() - t0, r.status, b[:18000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. auth 全部表: owner + relacl + RLS (哪些角色可读)
q("select c.relname, pg_get_userbyid(c.relowner) owner, c.relacl::text acl, c.relrowsecurity rls from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='auth' and c.relkind='r' order by 1;", "auth-acl")
# 2. read_only 通道身份 + pg_authid 读测 (区分 hook 范围)
q("select current_user cu, (select count(*) from pg_authid) n;", "ro-authid", read_only=True)
# 3. read_only 通道试读 auth.users (数据面权限确认)
q("select count(*) from auth.users;", "ro-users", read_only=True)
# 4. anon 角色对 auth 表的 SELECT 权限 (has_table_privilege 视角)
q("""select c.relname,
  has_table_privilege('anon', c.oid, 'SELECT') anon_sel,
  has_table_privilege('anon', c.oid, 'INSERT') anon_ins,
  has_table_privilege('authenticated', c.oid, 'SELECT') au_sel,
  has_table_privilege('postgres', c.oid, 'SELECT') pg_sel
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='auth' and c.relkind='r'
order by anon_sel desc, c.relname;""", "auth-haspriv")
# 5. pg_cron job 面确认 (建一个无害的现在执行一次的 job 再删)
q("select cron.unschedule((select jobid from cron.job where jobname='sbx_probe_cron' limit 1));", "cron-preclean")
q("select cron.schedule('sbx_probe_cron', 'select 1') jid;", "cron-sched")
q("select jobid, jobname, schedule, command, username, active from cron.job;", "cron-jobs")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb42_authacl.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:9000])
