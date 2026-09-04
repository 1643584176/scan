# -*- coding: utf-8 -*-
"""波11b:transaction action 正确 payload(sql 字段)语义"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def req(action, sql, timeout=90):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': action, 'sql': sql}
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
    return st, raw[:400].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# U1: transaction + 多语句
s, b, dt = req('transaction', 'select 1; select 2')
print('U1_tx_multi      [%d] %.1fs %s' % (s, dt, b[:200]))
# U2: transaction + DO 块
s, b, dt = req('transaction', "do $$ begin perform 1; end $$")
print('U2_tx_do         [%d] %.1fs %s' % (s, dt, b[:200]))
# U3: transaction + DML 提交性(insert 后 query 读)
s, b, dt = req('transaction', "create table if not exists tx_t(id int)")
print('U3_tx_ddl        [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = req('transaction', "insert into tx_t values (51)")
print('U3b_tx_insert    [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = req('query', 'select * from tx_t')
print('U3c_visible      [%d] %.1fs %s' % (s, dt, b[:200]))
# U4: transaction + 显式 rollback(观察是否真事务)
s, b, dt = req('transaction', "begin; insert into tx_t values (52); rollback")
print('U4_tx_rollback   [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = req('query', 'select * from tx_t')
print('U4b_after        [%d] %.1fs %s' % (s, dt, b[:200]))
# U5: transaction + 中途错误
s, b, dt = req('transaction', "insert into tx_t values (53); select 1/0")
print('U5_tx_err        [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = req('query', 'select * from tx_t')
print('U5b_after        [%d] %.1fs %s' % (s, dt, b[:200]))
# U6: 清理
s, b, dt = req('query', 'drop table if exists tx_t')
print('U6_cleanup       [%d] %.1fs %s' % (s, dt, b[:120]))
