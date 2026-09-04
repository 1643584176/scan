# -*- coding: utf-8 -*-
"""环境盘点: 分支/数据库/连接串 + 建源数据表(通过连接)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'

def req(tag, path, body=None, method=None):
    m = method or ('POST' if body is not None else 'GET')
    for attempt in range(2):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(m, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read()
            c.close()
            print('\n== %s -> %d' % (tag, r.status))
            print(raw[:900].decode('utf-8', errors='replace'))
            return r.status, raw
        except Exception as e:
            print('[retry]', e); time.sleep(2)
    return None, None

req('branches', '/projects/%s/branches' % P)
req('databases', '/projects/%s/branches/br-wandering-field-w2ob6mpn/databases' % P)
req('connection_uri', '/projects/%s/connection_uri?database_name=neondb' % P)
req('connection_uri2', '/projects/%s/connection_uri?database_name=neondb&pooled=true' % P)
