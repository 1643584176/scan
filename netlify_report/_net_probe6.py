# -*- coding: utf-8 -*-
"""Netlify 侦察 6:匿名探测 /access-control/* 与 featureflags"""
import http.client, ssl, gzip, brotli

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

print('=== app.netlify.com /access-control/* ===')
for p in ['/access-control/bb-api', '/access-control/analytics-api', '/access-control/analytics-api/',
          '/access-control/bb-api/', '/access-control/', '/access-control/health', '/access-control/api']:
    try:
        s, raw, hdrs = get('app.netlify.com', p)
        print('%-38s %d ct=%s body=%s' % (p, s, hdrs.get('content-type', '')[:25],
                                          raw[:80].decode('utf-8', 'ignore').replace('\n', ' ')[:70]))
    except Exception as e:
        print('%-38s ERR %s' % (p, str(e)[:50]))

print()
print('=== featureflags.netlify.com ===')
for p in ['/', '/api', '/api/flags', '/health', '/api/v1/flags']:
    try:
        s, raw, hdrs = get('featureflags.netlify.com', p)
        print('%-20s %d ct=%s body=%s' % (p, s, hdrs.get('content-type', '')[:25],
                                          raw[:80].decode('utf-8', 'ignore').replace('\n', ' ')[:70]))
    except Exception as e:
        print('%-20s ERR %s' % (p, str(e)[:50]))
