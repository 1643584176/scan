# -*- coding: utf-8 -*-
"""Netlify:调用账号 B 站点的函数"""
import http.client, ssl, gzip, brotli, sys, json, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()

name = sys.argv[1] if len(sys.argv) > 1 else 'probe7'
outfile = sys.argv[2] if len(sys.argv) > 2 else None
timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 90

conn = http.client.HTTPSConnection('sec-b-08v4pk.netlify.app', context=ctx, timeout=timeout)
conn.request('GET', '/.netlify/functions/%s' % name)
r = conn.getresponse()
b = r.read()
print('invoke', name, ':', r.status, 'len', len(b))
if outfile and r.status == 200:
    open(outfile, 'w', encoding='utf-8').write(b.decode('utf-8', 'replace'))
    print('saved', outfile)
elif r.status != 200:
    print(b[:800].decode('utf-8', 'replace'))
conn.close()
