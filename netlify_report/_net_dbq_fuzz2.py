# -*- coding: utf-8 -*-
"""database-query 变异第二轮:check 执行性 + transaction/queries 结构"""
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
        print('%-46s %d %s' % (label, s, raw[:250].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-46s ERR %s' % (label, str(e)[:60]))

T = 't_checkx%d' % int(time.time())  # 唯一表名
print('== test table:', T)
# B1. check 是否真执行:建表
show('check create table',     {'siteId': SITE_A, 'action': 'check', 'sql': 'create table if not exists %s(id int, v text)' % T})
# 若建表成功,query 应能 select 到
show('query select table',     {'siteId': SITE_A, 'action': 'query', 'sql': 'select count(*) from %s' % T})
# B2. check 中多语句是否执行(建第二个表)
T2 = T + '_b'
show('check multi create',     {'siteId': SITE_A, 'action': 'check', 'sql': 'create table if not exists %s(id int); create table if not exists %s(id int)' % (T2, T2)})
show('query check table2',     {'siteId': SITE_A, 'action': 'query', 'sql': 'select count(*) from %s' % T2})
# B3. transaction + queries 结构枚举
show('tx queries arr-obj',     {'siteId': SITE_A, 'action': 'transaction', 'queries': [{'sql': 'select 1'}]})
show('tx queries arr-str',     {'siteId': SITE_A, 'action': 'transaction', 'queries': ['select 1']})
show('tx queries str',         {'siteId': SITE_A, 'action': 'transaction', 'queries': 'select 1'})
show('tx queries obj',         {'siteId': SITE_A, 'action': 'transaction', 'queries': {'sql': 'select 1'}})
show('tx queries 2x',          {'siteId': SITE_A, 'action': 'transaction', 'queries': ['select 1', 'select 2']})
show('tx queries insert',      {'siteId': SITE_A, 'action': 'transaction', 'queries': ['insert into %s values (1, %s)' % (T2, "'tx1'"), 'select * from %s' % T2]})
# B4. check 无 siteId / 无 sql
show('check missing sql',      {'siteId': SITE_A, 'action': 'check'})
show('check empty sql',        {'siteId': SITE_A, 'action': 'check', 'sql': ''})
show('tx missing queries',     {'siteId': SITE_A, 'action': 'transaction', 'sql': 'select 1'})
