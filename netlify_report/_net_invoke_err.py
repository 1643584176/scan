# -*- coding: utf-8 -*-
"""查看函数错误响应体"""
import http.client, ssl, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=60)
conn.request('GET', '/.netlify/functions/probe4', headers={'Authorization': 'Bearer ' + TOKEN_A})
r = conn.getresponse()
b = r.read()
print('status:', r.status)
print(b.decode('utf-8', 'replace'))
conn.close()
