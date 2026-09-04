# -*- coding: utf-8 -*-
"""带 B cookie 直接请求 /file/{FILE_B} 编辑器页,提取 figma_app 主 bundle hash"""
import http.client, ssl, re, gzip, brotli

FILE_B = 'uwNXWhteG3ajjX78QG7a1W'
HOST = 'www.figma.com'

# 从 _figma_creds.py 导入 COOKIE_B
import sys, time
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B
TSID = 'mk' + str(int(time.time() * 1000))[-14:]

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=30)
path = '/file/%s' % FILE_B
headers = {
    'Host': HOST,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cookie': COOKIE_B,
    'tsid': TSID,
    'x-csrf-bypass': 'yes',
    'x-figma-client-version': '24850ed350d86c5466f8b775996885ec28db9f19',
    'x-figma-user-id': '1667396392129259941',
    'Origin': 'https://www.figma.com',
    'Referer': 'https://www.figma.com/',
}
conn.request('GET', path, headers=headers)
resp = conn.getresponse()
print('status:', resp.status, resp.reason)
print('url:', resp.getheader('X-Figma-*') or resp.getheader('Location'))
print('content-type:', resp.getheader('Content-Type'))
print('content-encoding:', resp.getheader('Content-Encoding'))
body = resp.read()
enc = resp.getheader('Content-Encoding')
if enc == 'br':
    body = brotli.decompress(body)
elif enc == 'gzip':
    body = gzip.decompress(body)
elif enc == 'deflate':
    import zlib
    body = zlib.decompress(body)
html = body.decode('utf-8', 'ignore')
print('body len:', len(html))
open('D:/scan/figma_report/_js/app_file_b.html', 'w', encoding='utf-8').write(html)

# 找 figma_app 主 bundle
for m in re.finditer(r'figma_app[^"\']{0,100}', html):
    print('figma_app:', m.group(0)[:120])
print()
for m in re.finditer(r'<script[^>]*src="([^"]+)"', html):
    u = m.group(1)
    if 'figma_app' in u or 'runtime' in u or 'assets' in u:
        print('script:', u[:160])
