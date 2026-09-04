# -*- coding: utf-8 -*-
"""解析应用 HTML(HTML unescape),下载主 bundle"""
import sys, re, os, ssl, http.client, brotli, html, requests, urllib3
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, FILE_B
urllib3.disable_warnings()

OUT = 'D:/scan/figma_report/_js/'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Cookie': COOKIE_B, 'Accept-Encoding': 'br, gzip'})

r = S.get('https://www.figma.com/file/%s' % FILE_B, timeout=15, verify=False)
html_doc = r.text
# 处理实体:&#47; -> /
scripts = [html.unescape(s) for s in re.findall(r'<script[^>]+src="([^"]+)"', html_doc)]
print('scripts:', len(scripts))
for s in scripts:
    print('  ', s[:130])
# 保存 HTML 供后续分析(所有 script/link)
with open(os.path.join(OUT, 'app_file.html'), 'w', encoding='utf-8') as f:
    f.write(html_doc)

# 下载所有 webpack-artifacts 引用
ctx = ssl.create_default_context()
for u in scripts:
    if '/webpack-artifacts/' not in u:
        continue
    fn = u.split('/')[-1].replace('.br', '')
    out_js = os.path.join(OUT, fn)
    if os.path.exists(out_js) and os.path.getsize(out_js) > 10000:
        print('exists:', fn)
        continue
    conn = http.client.HTTPSConnection('www.figma.com', context=ctx, timeout=90)
    conn.request('GET', u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                    'Accept-Encoding': 'br, gzip', 'Cookie': COOKIE_B})
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    if resp.status == 200 and body:
        enc = resp.getheader('Content-Encoding', '')
        try:
            data = brotli.decompress(body) if 'br' in enc else body
            with open(out_js, 'wb') as f:
                f.write(data)
            print('DL %s -> %d' % (fn, len(data)))
        except Exception as ex:
            print('decode fail %s: %s' % (fn, str(ex)[:40]))
    else:
        print('FAIL %s -> %d' % (fn, resp.status))
