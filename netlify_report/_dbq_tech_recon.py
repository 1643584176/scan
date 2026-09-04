# -*- coding: utf-8 -*-
"""数据库技术层侦察(纯只读):
1. pg_available_extensions 全清单
2. 已安装扩展 + 属主
3. 全部 SECURITY DEFINER 函数(owner/schema/语言)
4. 各 schema owner + netlifydb_owner 的 CREATE 权限
5. 扩展 schema 内可写对象"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=60)
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
    out = raw[:3000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


tests = [
    ('可用扩展(名称/版本/注释)', "select name, default_version, installed_version from pg_available_extensions where name in "
     "(select name from pg_available_extensions) order by name"),
    ('可用扩展总数', "select count(*) from pg_available_extensions"),
    ('已安装扩展', "select e.extname, e.extversion, n.nspname as schema, r.rolname as owner from pg_extension e "
     "join pg_namespace n on e.extnamespace=n.oid join pg_roles r on e.extowner=r.oid order by 1"),
    ('DEFINER 函数', "select n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' as fn, "
     "r.rolname as owner from pg_proc p join pg_namespace n on p.pronamespace=n.oid "
     "join pg_roles r on p.proowner=r.oid where p.prosecdef and n.nspname not in ('pg_catalog','information_schema') "
     "order by r.rolname, n.nspname"),
    ('schema owner+CREATE', "select n.nspname, r.rolname as owner, "
     "has_schema_privilege('netlifydb_owner', n.nspname, 'CREATE') as owner_can_create, "
     "has_schema_privilege('netlifydb_owner', n.nspname, 'USAGE') as owner_can_use "
     "from pg_namespace n join pg_roles r on n.nspowner=r.oid "
     "where n.nspname not in ('pg_catalog','information_schema','pg_toast') order by n.nspname"),
]
for desc, sql in tests:
    st, out = q(sql)
    print('==== %s [%d] ====' % (desc, st))
    print(out[:2800])
    print()
