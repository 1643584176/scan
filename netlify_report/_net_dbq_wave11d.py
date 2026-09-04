# -*- coding: utf-8 -*-
"""波11d:transaction 语义全测(原子性/提交/错误中断/元素内多语句)"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def req_tx(qs, timeout=120):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': 'transaction', 'queries': [{'sql': q} for q in qs]}
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


def req_q(sql, timeout=90):
    return req_tx([sql]) if False else _q(sql, timeout)


def _q(sql, timeout=90):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Cookie': COOKIE_NET, 'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': 'query', 'sql': sql}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    conn.close()
    return r.status, raw[:300].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# W1: DDL+DML 原子性(中途错误)
s, b, dt = req_tx(['drop table if exists tx2', 'create table tx2(id int)',
                   'insert into tx2 values (1)', 'select 1/0', 'insert into tx2 values (2)'])
print('W1_tx_err_mid    [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = _q('select * from tx2')
print('W1b_after        [%d] %.1fs %s' % (s, dt, b[:200]))
# W2: 无错误提交
s, b, dt = req_tx(['drop table if exists tx2', 'create table tx2(id int)', 'insert into tx2 values (10)'])
print('W2_tx_commit     [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = _q('select * from tx2')
print('W2b_visible      [%d] %.1fs %s' % (s, dt, b[:200]))
# W3: 元素内多语句(prepared 限制在 transaction 模式是否还在)
s, b, dt = req_tx(['select 1; select 2'])
print('W3_elem_multi    [%d] %.1fs %s' % (s, dt, b[:200]))
# W4: 元素内 DO
s, b, dt = req_tx(["do $$ begin perform pg_sleep(2); perform 1; end $$", 'select 3'])
print('W4_do_then       [%d] %.1fs %s' % (s, dt, b[:200]))
# W5: 错误元素后继续执行?
s, b, dt = req_tx(['select 1', 'selct 2', 'select 3'])
print('W5_err_continue  [%d] %.1fs %s' % (s, dt, b[:250]))
# W6: 事务边界 — 元素间可见性(同事务内:insert 后 select 能看到?)
s, b, dt = req_tx(['drop table if exists tx2', 'create table tx2(id int)', 'insert into tx2 values (99)', 'select * from tx2'])
print('W6_intra_visible [%d] %.1fs %s' % (s, dt, b[:250]))
# W7: 元素内事务控制语句
s, b, dt = req_tx(['begin', 'insert into tx2 values (100)', 'commit'])
print('W7_tx_ctrl       [%d] %.1fs %s' % (s, dt, b[:200]))
s, b, dt = _q('select * from tx2')
print('W7b_after        [%d] %.1fs %s' % (s, dt, b[:250]))
# W8: 清理
s, b, dt = _q('drop table if exists tx2')
print('W8_cleanup       [%d] %.1fs %s' % (s, dt, b[:100]))
