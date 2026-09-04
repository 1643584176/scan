# -*- coding: utf-8 -*-
"""精确清理:删除 t_tx*/t_checkx* 表与 probe_zzz 角色"""
import http.client, ssl, gzip, brotli, json, sys, re
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
    return st, raw.decode('utf-8', 'ignore').replace('\n', ' ')

st, raw = q("select table_name from information_schema.tables where table_schema='public'")
print('before:', raw[:400])
names = re.findall(r'"table_name":"([^"]+)"', raw)
for n in names:
    if n.startswith(('t_tx', 't_checkx')):
        st2, raw2 = q('drop table if exists %s' % n)
        print('drop %s -> %d %s' % (n, st2, raw2[:80]))
st, raw = q("select rolname from pg_roles where rolname like 'probe%'")
print('roles:', raw[:200])
for rn in re.findall(r'"rolname":"([^"]+)"', raw):
    st2, raw2 = q('drop role if exists %s' % rn)
    print('drop role %s -> %d %s' % (rn, st2, raw2[:80]))
