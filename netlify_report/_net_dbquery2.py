# -*- coding: utf-8 -*-
"""Netlify:database-query sql 字段完整测试"""
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
    ('query select 1', {'siteId': SITE_ID, 'action': 'query', 'sql': 'select 1'}),
    ('query create table', {'siteId': SITE_ID, 'action': 'query', 'sql': 'create table if not exists t1(id int, secret text)'}),
    ('query insert', {'siteId': SITE_ID, 'action': 'query', 'sql': "insert into t1 values (1, 'hello')"}),
    ('query select *', {'siteId': SITE_ID, 'action': 'query', 'sql': 'select * from t1'}),
    ('query multi-statement', {'siteId': SITE_ID, 'action': 'query', 'sql': 'select 1; select 2'}),
    ('query grant/priv', {'siteId': SITE_ID, 'action': 'query', 'sql': "select current_user, current_database(), version()"}),
    ('transaction', {'siteId': SITE_ID, 'action': 'transaction', 'sql': 'select 1'}),
]
for label, b in tests:
    try:
        s, raw = req(P, body=b)
        body = raw[:250].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-26s %d %s' % (label, s, body))
    except Exception as e:
        print('%-26s ERR %s' % (label, str(e)[:50]))
