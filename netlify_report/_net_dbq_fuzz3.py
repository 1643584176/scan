# -*- coding: utf-8 -*-
"""database-query 变异第三轮:transaction queries 元素结构/多元素/参数化"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def req(body):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Content-Type': 'application/json'}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

def show(label, body):
    try:
        s, raw = req(body)
        print('%-50s %d %s' % (label, s, raw[:280].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-50s ERR %s' % (label, str(e)[:60]))

T = 't_tx%d' % int(time.time())
print('== table:', T)
# C1. 多元素 arr-obj
show('tx 2x arr-obj',         {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': 'select 1'}, {'sql': 'select 2'}]})
# C2. 元素内多语句(驱动拦截是否同样存在)
show('tx elem multi-semi',    {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': 'select 1; select 2'}]})
# C3. 元素字段名变体
show('tx elem query key',     {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'query': 'select 1'}]})
show('tx elem stmt key',      {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'statement': 'select 1'}]})
show('tx elem text key',      {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'text': 'select 1'}]})
show('tx elem name+s',        {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'name': 'a', 'sql': 'select 1'}]})
show('tx elem params',        {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': 'select $1', 'params': ['x']}]})
show('tx elem params arr',    {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': 'select $1::int', 'params': [1]}]})
# C4. 事务 DDL/回滚观察
show('tx create+select',      {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': 'create table if not exists %s(id int)' % T}, {'sql': "insert into %s values (1)" % T}, {'sql': 'select * from %s' % T}]})
show('query after tx',        {'siteId': SITE_A, 'action': 'query', 'sql': 'select count(*) from %s' % T})
# C5. 错误中途回滚?第一句错第二句建表
show('tx err then create',    {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': 'select bad_col from nope'}, {'sql': 'create table if not exists %s(id int)' % T}]})
show('query after err-tx',    {'siteId': SITE_A, 'action': 'query', 'sql': 'select count(*) from %s' % T})
