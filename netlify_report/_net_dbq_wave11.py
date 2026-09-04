# -*- coding: utf-8 -*-
"""波11:transaction action 语义面(queries 数组=官方多语句通道)
T1 多条查询 / T2 DML+提交可见性 / T3 事务控制语句注入 / T4 回滚 / T5 组合
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def req(action, payload_extra, timeout=90):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = dict({'siteId': SITE_ID, 'action': action}, **payload_extra)
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
    return st, raw[:500].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# T1: 多条查询
s, b, dt = req('transaction', {'queries': ['select 1 as a', 'select 2 as b']})
print('T1_multi_select  [%d] %.1fs %s' % (s, dt, b[:200]))
# T2: DML 事务 + 跨 action 可见性(先事务插入,再 query 读)
s, b, dt = req('transaction', {'queries': ["create table if not exists tx_t(id int)", "insert into tx_t values (42)"]})
print('T2_tx_dml        [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = req('query', {'sql': 'select * from tx_t'})
print('T2b_visible      [%d] %.1fs %s' % (s, dt, b[:200]))
# T3: queries 里放事务控制语句
s, b, dt = req('transaction', {'queries': ['begin', 'select 1', 'commit']})
print('T3_tx_ctrl       [%d] %.1fs %s' % (s, dt, b[:200]))
# T4: rollback 语义(insert 后 rollback,应不可见)
s, b, dt = req('transaction', {'queries': ['insert into tx_t values (43)', 'rollback']})
print('T4_rollback      [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = req('query', {'sql': 'select count(*) from tx_t'})
print('T4b_count        [%d] %.1fs %s' % (s, dt, b[:200]))
# T5: 错误中断语义(第一条错,后续执行吗?)
s, b, dt = req('transaction', {'queries': ['select 1/0', 'select 99']})
print('T5_err_mid       [%d] %.1fs %s' % (s, dt, b[:200]))
# T6: DO + sleep 在事务数组里(时序)
s, b, dt = req('transaction', {'queries': ['select pg_sleep(3)', 'select 7']})
print('T6_sleep         [%d] %.1fs %s' % (s, dt, b[:200]))
# T7: 数组元素里塞多语句(元素内部)
s, b, dt = req('transaction', {'queries': ['select 1; select 2']})
print('T7_elem_multi    [%d] %.1fs %s' % (s, dt, b[:200]))
