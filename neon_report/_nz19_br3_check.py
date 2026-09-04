# -*- coding: utf-8 -*-
"""连 br3: 检查脱敏结果 + anon 扩展对象面"""
import http.client, ssl, json, time, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
BR3 = 'br-rapid-lake-w2aky5fq'

def req(path):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request('GET', API_BASE + path, headers=h)
            r = c.getresponse(); raw = r.read()
            c.close()
            return r.status, raw
        except Exception as e:
            time.sleep(2)
    return None, None

st, raw = req('/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s' % (P, BR3))
uri = json.loads(raw).get('uri', '')
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
parts = urlsplit(uri)
q = [(k, v) for k, v in parse_qsl(parts.query) if k != 'channel_binding']
uri = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))
print('uri ->', st)

import psycopg
with psycopg.connect(uri, connect_timeout=20) as conn:
    conn.autocommit = True
    cur = conn.cursor()
    # 脱敏结果
    cur.execute('select id, email, full_name, secret from public.sbx_anon_src order by id')
    print('\n-- masked data:')
    for row in cur.fetchall():
        print('  ', row)
    # 扩展
    cur.execute("""select e.extname, e.extversion, r.rolname as ext_owner
        from pg_extension e join pg_roles r on r.oid = e.extowner order by 1""")
    print('\n-- extensions:')
    for row in cur.fetchall():
        print('  ', row)
    # anon 函数 (secdef 重点)
    cur.execute("""select n.nspname, p.proname, p.prosecdef, r.rolname as fn_owner,
        pg_get_function_identity_arguments(p.oid) as args
        from pg_proc p join pg_namespace n on n.oid=p.pronamespace
        join pg_roles r on r.oid=p.proowner
        where n.nspname like 'anon%' order by n.nspname, p.proname limit 60""")
    print('\n-- anon functions:')
    for row in cur.fetchall():
        print('  ', row)
    # 当前用户与 anon 角色
    cur.execute('select current_user, session_user')
    print('\n-- current:', cur.fetchall())
    cur.execute("""select rolname, rolsuper, rolcreatedb, rolcreaterole, rolcanlogin from pg_roles
        where rolname like 'anon%' or rolname in ('cloud_admin','neon_superuser')""")
    print('-- roles:', cur.fetchall())
