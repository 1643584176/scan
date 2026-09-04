# -*- coding: utf-8 -*-
"""Netlify:database-query 内部函数测试(自己 siteId + 越权对比)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def req(path, method='POST', body=None, headers=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
    if headers:
        h.update(headers)
    conn.request(method, path, body=body, headers=h)
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

P = '/.netlify/functions/database-query'
tests = [
    ('check(自己)', {'siteId': SITE_ID, 'action': 'check'}),
    ('query(自己) select 1', {'siteId': SITE_ID, 'action': 'query', 'query': 'select 1'}),
    ('query(自己) create table', {'siteId': SITE_ID, 'action': 'query', 'query': 'create table if not exists t1(id int)'}),
    ('query(自己) insert', {'siteId': SITE_ID, 'action': 'query', 'query': "insert into t1 values (1)"}),
    ('query(自己) select t1', {'siteId': SITE_ID, 'action': 'query', 'query': 'select * from t1'}),
    ('transaction(自己)', {'siteId': SITE_ID, 'action': 'transaction', 'queries': ['select 1']}),
    # 越权候选:其他 siteId 格式(不存在的)
    ('check(不存在site)', {'siteId': '00000000-0000-0000-0000-000000000000', 'action': 'check'}),
    ('query(不存在site)', {'siteId': '00000000-0000-0000-0000-000000000000', 'action': 'query', 'query': 'select 1'}),
]
for label, b in tests:
    try:
        s, raw = req(P, body=b)
        body = raw[:200].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-28s %d %s' % (label, s, body))
    except Exception as e:
        print('%-28s ERR %s' % (label, str(e)[:50]))
