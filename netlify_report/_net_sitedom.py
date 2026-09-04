# -*- coding: utf-8 -*-
"""Netlify:站点域 .netlify/* 平台路径探测(自己站点,含图片 CDN url 参数)"""
import http.client, ssl, gzip, brotli, sys, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')

ctx = ssl.create_default_context()

def req(host, path, headers=None, method='GET'):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip'}
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
    loc = hdrs.get('location', '')
    conn.close()
    return st, raw, hdrs

SITE_HOST = 'sec-test-rcf6lz.netlify.app'

print('=== 站点域 .netlify/* ===')
for p in ['/.netlify/images',
          '/.netlify/images?url=https%3A%2F%2Fexample.com%2Ftest.png',
          '/.netlify/images?url=http%3A%2F%2Fexample.com%2Ftest.png',
          '/.netlify/images?url=file%3A%2F%2F%2Fetc%2Fpasswd',
          '/.netlify/images?url=',
          '/.netlify/functions/test',
          '/.netlify/identity',
          '/.netlify/identity/login',
          '/.netlify/identity/signup',
          '/.netlify/large-media',
          '/.netlify/large-media/upload',
          '/.netlify/edge-functions/test',
          '/.netlify/edge-functions',
          '/.netlify/status',
          '/.netlify/health',
          '/.netlify/deploy',
          '/.netlify/builders',
          '/.netlify/redirects',
          '/.netlify/config',
          '/.netlify/telemetry',
          '/_headers',
          '/_redirects',
          '/.netlify/functions/',
          '/.netlify/plugins',
          '/.netlify/plugins/versions',
          '/.netlify/serverless',
          '/.netlify/serverless_deprecations',
          '/.netlify/edge-handler',
          '/.netlify/handlers',
          '/.netlify/package.json',
          '/.netlify/functions-internal',
          '/.netlify/state.json',
          '/.netlify/.env',
          '/.env',
          '/.git/config',
          '/robots.txt',
          '/sitemap.xml']:
    try:
        s, raw, hdrs = req(SITE_HOST, p)
        ct = hdrs.get('content-type', '')[:40]
        print('%-52s %d %-42s %s' % (p, s, ct, raw[:60].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-52s ERR %s' % (p, str(e)[:40]))
