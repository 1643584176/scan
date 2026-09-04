# -*- coding: utf-8 -*-
"""Netlify 侦察 2:app.netlify.com + api.netlify.com 匿名探测"""
import http.client, ssl, gzip, brotli, re

ctx = ssl.create_default_context()

def get(host, path, headers=None, method='GET'):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip'}
    if headers:
        h.update(headers)
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    conn.close()
    return st, raw, hdrs

# 1. app.netlify.com
s, raw, hdrs = get('app.netlify.com', '/')
print('app.netlify.com:', s, 'len', len(raw))
for k in ['server', 'set-cookie', 'x-nf-request-id']:
    if k in hdrs:
        print('  %s: %s' % (k, str(hdrs[k])[:150]))
txt = raw.decode('utf-8', 'ignore')
open(r'D:\scan\netlify_report\_js\net_app.html', 'w', encoding='utf-8').write(txt)
for m in list(re.finditer(r'<script[^>]+src="([^"]+)"', txt))[:15]:
    print('JS:', m.group(1)[:140])
print()

# 2. api.netlify.com 匿名探测
print('=== api.netlify.com 匿名 ===')
paths = ['/api/v1/sites', '/api/v1/user', '/api/v1/accounts', '/api/v1/forms',
         '/.netlify/functions', '/api/v1/', '/api/v1/sites?per_page=1', '/api/v1/deploys']
for p in paths:
    try:
        s, raw, hdrs = get('api.netlify.com', p)
        print('%-32s %d ct=%s body=%s' % (p, s, hdrs.get('content-type', '')[:25],
                                          raw[:100].decode('utf-8', 'ignore').replace('\n', ' ')[:90]))
    except Exception as e:
        print('%-32s ERR %s' % (p, str(e)[:50]))
