# -*- coding: utf-8 -*-
"""连通性 + staging API key 验证 (1 请求)"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']

ctx = ssl.create_default_context()
t0 = time.time()
try:
    c = http.client.HTTPSConnection(API_HOST, timeout=15, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    c.request('GET', API_BASE + '/projects', headers=h)
    r = c.getresponse()
    b = r.read(3000).decode('utf-8', errors='replace')
    print('[%.1fs] %d' % (time.time() - t0, r.status))
    print(b[:1500])
    c.close()
except Exception as e:
    print('ERR', e)
