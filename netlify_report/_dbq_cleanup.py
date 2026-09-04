# -*- coding: utf-8 -*-
"""清理 database-query 变异测试残留(自己的库)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def q(sql):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Cookie': COOKIE_A, 'Content-Type': 'application/json'}
    body = json.dumps({'siteId': SITE_A, 'action': 'query', 'sql': sql}).encode()
    conn.request('POST', '/.netlify/functions/database-query', body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw[:120].decode('utf-8', 'ignore').replace('\n', ' ')

for label, sql in [
    ('drop t1',          'drop table if exists t1'),
    ('drop t_checkx',    "select 'cleanup via loop'"),
    ('list tables',      "select table_name from information_schema.tables where table_schema='public'"),
]:
    print('%-14s %s %s' % (label, *q(sql)))
# 精确删除本会话创建的表
import re
st, raw = q("select table_name from information_schema.tables where table_schema='public'")
print('remaining:', raw[:300])
