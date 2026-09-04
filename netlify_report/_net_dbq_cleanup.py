# -*- coding: utf-8 -*-
"""database-query 攻破面清理:删除测试表 probe_t"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Content-Type': 'application/json',
     'Cookie': COOKIE_NET}
body = json.dumps({'siteId': SITE_ID, 'action': 'query', 'sql': 'drop table if exists probe_t'}).encode()
conn.request('POST', '/.netlify/functions/database-query', body=body, headers=h)
r = conn.getresponse()
raw = r.read()
print('cleanup:', r.status, raw[:200])
conn.close()
