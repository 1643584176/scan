# -*- coding: utf-8 -*-
"""波11c:transaction queries 元素结构探测(对象 vs 字符串)"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def req(payload, timeout=90):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = dict({'siteId': SITE_ID, 'action': 'transaction'}, **payload)
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


variants = [
    ('V1 obj sql',       {'queries': [{'sql': 'select 1'}, {'sql': 'select 2'}]}),
    ('V2 obj query',     {'queries': [{'query': 'select 1'}]}),
    ('V3 str',           {'queries': ['select 1']}),
    ('V4 mixed',         {'queries': [{'sql': 'select 1'}, 'select 2']}),
    ('V5 extra fields',  {'queries': [{'sql': 'select 1', 'name': 'a'}]}),
]
for label, pl in variants:
    s, b, dt = req(pl)
    print('%-16s [%d] %.1fs %s' % (label, s, dt, b[:180]))
