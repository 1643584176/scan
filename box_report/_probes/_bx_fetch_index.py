# -*- coding: utf-8 -*-
"""Fetch app.box.com entry HTML & extract JS bundle URLs (single low-volume request)."""
import re
import ssl
import http.client
import sys

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('app.box.com', 443, timeout=20, context=ctx)
conn.request('GET', '/', headers={'User-Agent': UA, 'Accept': 'text/html'})
r = conn.getresponse()
raw = r.read(3000000)
conn.close()
print('status:', r.status, 'ctype:', r.headers.get('Content-Type'))
body = raw.decode('utf-8', 'replace')

# js bundles
srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', body, re.I)
for s in srcs:
    print('SCRIPT:', s)
# css
for s in re.findall(r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']', body, re.I):
    print('CSS   :', s)
# link hints to api endpoints / meta
for m in re.findall(r'(https?://[a-z0-9.\-]*box\.com[^"\'\s<>]*)', body):
    if not any(x in m for x in ('.png', '.ico', '.css', '.woff', '.svg')):
        print('URL   :', m[:200])
sys.stdout.write('BODY_SAVED len=%d\n' % len(body))
open(r'F:/scan/box_report/_js/_app_box_index.html', 'w', encoding='utf-8').write(body)
