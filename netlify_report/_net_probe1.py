# -*- coding: utf-8 -*-
"""Netlify 侦察 1:抓 www.netlify.com 首页 + bundle 引用"""
import http.client, ssl, gzip, brotli, re

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('www.netlify.com', context=ctx, timeout=20)
conn.request('GET', '/', headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
    'Accept-Encoding': 'br, gzip'})
r = conn.getresponse()
raw = r.read()
enc = r.getheader('Content-Encoding')
if enc == 'br':
    raw = brotli.decompress(raw)
elif enc == 'gzip':
    raw = gzip.decompress(raw)
print('status:', r.status, 'len:', len(raw))
h = {k.lower(): v for k, v in r.getheaders()}
for k in ['server', 'x-powered-by', 'set-cookie', 'strict-transport-security', 'x-nf-request-id', 'x-frame-options']:
    if k in h:
        print('  %s: %s' % (k, str(h[k])[:200]))
conn.close()
txt = raw.decode('utf-8', 'ignore')
open(r'D:\scan\netlify_report\_js\net_index.html', 'w', encoding='utf-8').write(txt)
for m in list(re.finditer(r'<script[^>]+src="([^"]+)"', txt))[:12]:
    print('JS:', m.group(1)[:130])
