# -*- coding: utf-8 -*-
"""出站边界精确判定:
1. 旧 B endpoint(ep-cold-unit)通不通(轮换 vs 分支)
2. 公网 IP 1.1.1.1:5432 / 8.8.8.8:5432(白名单 vs 全通)
3. 公网 IP + 常见端口(22/443)区分协议限制
4. lakebase_text 函数修正查询"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()


def q(sql, timeout=50):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    body = {'siteId': SITE_A, 'action': 'query', 'sql': sql}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:400].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def fdw_test(label, host, port='5432', timeout=50):
    name = 'srv_t'
    # 用 dblink 单语句快速测(需要密码?dblink_connect 剥密码...用 FDW)
    st1, _ = q("create server if not exists %s foreign data wrapper postgres_fdw options (host '%s', port '%s', dbname 'x')" % (name, host, port), timeout)
    st2, out2 = q("select count(*) from pg_foreign_table ft join pg_foreign_server s on ft.ftserver=s.oid "
                  "join pg_foreign_data_wrapper w on s.srvfdw=w.oid", timeout)
    # 触发连接:import schema 或建 foreign table 读
    st3, out3 = q("create foreign table if not exists ft_t(id int) server %s options (schema_name 'public', table_name 'k_z')" % name, timeout)
    st4, out4 = q('select * from ft_t', timeout)
    q("drop foreign table if exists ft_t", timeout)
    q("drop server if exists %s cascade" % name, timeout)
    print('%-28s [%d|%d] %s' % (label, st3, st4, out4[:200]))


print('== 旧 endpoint 状态 ==')
fdw_test('旧 B ep-cold-unit', 'ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com')
fdw_test('A ep-autumn(自己)', 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com')
print()
print('== 公网 IP 出站 ==')
fdw_test('1.1.1.1:5432', '1.1.1.1')
fdw_test('8.8.8.8:5432', '8.8.8.8')
fdw_test('1.1.1.1:22', '1.1.1.1', '22')
fdw_test('1.1.1.1:443', '1.1.1.1', '443')
fdw_test('1.1.1.1:80', '1.1.1.1', '80')
print()
print('== 内网探测 ==')
fdw_test('169.254.169.254:5432(元数据)', '169.254.169.254')
fdw_test('10.0.0.1:5432', '10.0.0.1')
print()
print('== lakebase_text 函数(修正) ==')
st, out = q("select p.proname||'('||pg_get_function_identity_arguments(p.oid)||')', p.prosecdef "
            "from pg_proc p join pg_depend d on d.objid=p.oid and d.classid='pg_proc'::regclass "
            "join pg_extension e on d.refobjid=e.oid where e.extname='lakebase_text' order by 1")
print('[%d] %s' % (st, out[:1500]))
