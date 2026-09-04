# -*- coding: utf-8 -*-
"""用 B cookie 抓登录态首页,提取并下载主 bundle"""
import sys, re, os, ssl, http.client, brotli, requests, urllib3
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B
urllib3.disable_warnings()

OUT = 'D:/scan/figma_report/_js/'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Cookie': COOKIE_B, 'Accept-Encoding': 'br, gzip'})

r = S.get('https://www.figma.com/', timeout=15, verify=False)
print('status:', r.status_code, 'len:', len(r.text))
html = r.text
scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)
print('scripts:', len(scripts))
main = [s for s in scripts if 'figma_app' in s]
print('figma_app refs:', main[:5])

# 下载主 bundle
ctx = ssl.create_default_context()
for u in main:
    fn = u.split('/')[-1]
    out_js = os.path.join(OUT, fn.replace('.br', ''))
    if os.path.exists(out_js) and os.path.getsize(out_js) > 10000:
        print('exists:', out_js)
        continue
    conn = http.client.HTTPSConnection('www.figma.com', context=ctx, timeout=30)
    conn.request('GET', u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                    'Accept-Encoding': 'br, gzip', 'Cookie': COOKIE_B})
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    print('DL %s -> %d status %s' % (fn, len(body), resp.status))
    if resp.status == 200 and body:
        enc = resp.getheader('Content-Encoding', '')
        try:
            data = brotli.decompress(body) if 'br' in enc else body
            with open(out_js, 'wb') as f:
                f.write(data)
            print('  saved %s -> %d' % (out_js, len(data)))
        except Exception as e:
            print('  decode fail:', str(e)[:50])
