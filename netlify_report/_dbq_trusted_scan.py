# -*- coding: utf-8 -*-
"""技术层测试 6:
1. netlifydb_owner 角色属性(createdb/createrole/bypassrls/superuser 成员关系)
2. 批量 trusted 扩展试探(装→definer 检查→drop)
3. B endpoint 公网 IP 直连(出站网络判定:DNS 限制 or IP 层限制)"""
import http.client, ssl, gzip, brotli, json, sys, socket
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, timeout=40):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
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
    out = raw[:1200].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== 1. 角色属性 ==')
st, out = q("select rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolbypassrls, "
            "rolreplication, rolconnlimit from pg_roles where rolname in ('netlifydb_owner','netlifydb_readonly','cloud_admin','neon_superuser')")
print('[%d] %s' % (st, out[:600]))
st, out = q("select r.rolname from pg_roles r where pg_has_role('netlifydb_owner', r.oid, 'member') and r.rolname not like 'pg_%'")
print('netlifydb_owner 成员 [%d] %s' % (st, out[:400]))

print()
print('== 2. 批量扩展试探 ==')
cands = ['pgcrypto', 'hstore', 'ltree', 'unaccent', 'fuzzystrmatch', 'intarray', 'btree_gin',
         'btree_gist', 'cube', 'earthdistance', 'seg', 'bloom', 'isn', 'dict_int', 'dict_xsyn',
         'tablefunc', 'tsm_system_rows', 'tsm_system_time', 'autoinc', 'insert_username',
         'moddatetime', 'tcn', 'xml2', 'pgrowlocks', 'pg_visibility', 'pgstattuple', 'pg_trgm',
         'pg_prewarm', 'pg_stat_statements', 'lo', 'pg_freespacemap', 'uuid-ossp']
for ext in cands:
    st, out = q('create extension if not exists "' + ext + '"')
    if st == 200:
        st2, out2 = q("select count(*) from pg_proc p join pg_depend d on d.objid=p.oid and d.classid='pg_proc'::regclass "
                      "join pg_extension e on d.refobjid=e.oid where e.extname='" + ext + "' and p.prosecdef")
        st3, out3 = q("select p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' from pg_proc p "
                      "join pg_depend d on d.objid=p.oid and d.classid='pg_proc'::regclass "
                      "join pg_extension e on d.refobjid=e.oid where e.extname='" + ext + "' and p.prosecdef")
        print('%-18s 可装 definer=%s %s' % (ext, out2[:60], out3[:200]))
        q('drop extension if exists "' + ext + '" cascade')
    else:
        print('%-18s 拒 [%d] %s' % (ext, st, out[:110]))

print()
print('== 3. B endpoint IP ==')
try:
    ip = socket.gethostbyname('ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com')
    print('B IP =', ip)
except Exception as e:
    print('resolve err', e)
try:
    ip2 = socket.gethostbyname('ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com')
    print('A IP =', ip2)
except Exception as e:
    print('resolve err', e)
