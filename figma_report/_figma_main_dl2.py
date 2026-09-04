# -*- coding: utf-8 -*-
"""下载 figma_app 主 bundle + runtime,提取 livegraph view 名"""
import http.client, ssl, brotli, re, os

HOST = 'www.figma.com'
OUT = 'D:/scan/figma_report/_js/'
files = [
    'runtime~figma_app-544f4cf67e944191.min.js.br',
    'figma_app-60cc81284aa4afb8.min.js.br',
    'vendor-core-1e0448b648ed4863.min.js.br',
]

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=60)
for f in files:
    p = os.path.join(OUT, f)
    if os.path.exists(p):
        print(f, 'cached'); continue
    conn.request('GET', '/webpack-artifacts/assets/' + f,
                 headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                          'Accept-Encoding': 'br, gzip',
                          'Referer': 'https://www.figma.com/'})
    resp = conn.getresponse()
    body = resp.read()
    print(f, 'status', resp.status, 'enc', resp.getheader('Content-Encoding'), 'raw', len(body))
    if resp.status == 200:
        open(p, 'wb').write(body)

print()
# 解压主 bundle
main = os.path.join(OUT, 'figma_app-60cc81284aa4afb8.min.js.br')
d = brotli.decompress(open(main, 'rb').read()).decode('utf-8', 'ignore')
print('main bundle len:', len(d))
open(os.path.join(OUT, 'figma_app-main.js'), 'w', encoding='utf-8').write(d)

# 提取 View 名:形如 XxxView(identifier 常量)
views = set(re.findall(r'[A-Z][A-Za-z0-9]{2,60}View\b', d))
print('View names:', len(views))
for v in sorted(views):
    print('  ', v)
