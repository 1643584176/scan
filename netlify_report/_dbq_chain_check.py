# -*- coding: utf-8 -*-
"""A 库链现场检查 + health_check 表详情(只读)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A, COOKIE_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, cookie=COOKIE_A, site=SITE_A):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=45)
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
    out = raw[:1500].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== A 链现场 ==')
st, out = q("select n.nspname||'.'||c.relname from pg_class c join pg_namespace n on c.relnamespace=n.oid "
            "where c.relname like 'k\\_%' or c.relname like 'log\\_%' or c.relname like 't\\_%' or c.relname like 'pk\\_%'")
print('k/log/t 对象 [%d] %s' % (st, out[:800]))
st, out = q("select tgname from pg_trigger where not tgisinternal")
print('触发器 [%d] %s' % (st, out[:600]))
st, out = q("select proname from pg_proc where proname like 'k\\_%' or proname like 'evil%'")
print('函数 [%d] %s' % (st, out[:600]))
st, out = q("select extname from pg_extension where extname='pg_repack'")
print('pg_repack [%d] %s' % (st, out[:300]))

print()
print('== health_check 表(A/B) ==')
st, out = q("select c.relname, c.relowner::regrole from pg_class c where c.relname='health_check'")
print('A [%d] %s' % (st, out[:400]))
st, out = q("select c.relname, c.relowner::regrole, c.relrowsecurity from pg_class c where c.relname='health_check'",
            cookie=COOKIE_B, site=SITE_B)
print('B [%d] %s' % (st, out[:400]))
st, out = q("select column_name, data_type from information_schema.columns where table_name='health_check' order by ordinal_position",
            cookie=COOKIE_B, site=SITE_B)
print('B cols [%d] %s' % (st, out[:600]))
st, out = q("select * from health_check", cookie=COOKIE_B, site=SITE_B)
print('B rows [%d] %s' % (st, out[:600]))
