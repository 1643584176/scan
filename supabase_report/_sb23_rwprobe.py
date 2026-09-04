# -*- coding: utf-8 -*-
"""v1 database/query 非只读通道盘点 (SQL 全只读零破坏)"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def q(sql, tag, ro=False):
    body = json.dumps({"query": sql, "read_only": ro})
    c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(4000).decode('utf-8', errors='replace')
        out.append('### [%s|ro=%s] %s (%.1fs)\n%s | %s' % (tag, ro, sql[:80], time.time() - t0, r.status, b[:2000]))
        c.close()
    except Exception as e:
        out.append('### [%s] %s ERR %s' % (tag, sql[:80], e))

q("select current_user cu, session_user su, current_setting('role') rc, current_setting('is_superuser') su_;", "identity", ro=False)
q("select rolname, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolcanlogin from pg_roles order by 1;", "roles", ro=False)
q("select count(*) n from pg_authid;", "authid", ro=False)
q("select pg_read_file('/etc/passwd',0,200) f;", "readfile", ro=False)
q("select extname, extversion from pg_extension order by 1;", "ext", ro=False)
q("select nspname from pg_namespace where nspname not like 'pg\\_%' and nspname <> 'information_schema' order by 1;", "schema", ro=False)
q("select name, default_version, installed_version from pg_available_extensions where name ilike '%supa%' or name in ('postgres_fdw','wrappers','pg_net','pg_cron','pgsodium','pg_graphql','pg_tle','hypopg','plpgsql') order by 1;", "avail", ro=False)
q("select name, setting from pg_settings where name in ('data_directory','dynamic_library_path','log_directory','server_version_num','port');", "settings", ro=False)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb23_rwprobe.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:7000])
