# -*- coding: utf-8 -*-
"""带 cookie 请求文件页/应用页,提取主 bundle URL 并下载"""
import sys, re, os, ssl, http.client, brotli, requests, urllib3
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, FILE_B
urllib3.disable_warnings()

OUT = 'D:/scan/figma_report/_js/'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Cookie': COOKIE_B, 'Accept-Encoding': 'br, gzip'})

for path in ['/file/%s' % FILE_B, '/make/%s' % FILE_B, '/desk/']:
    r = S.get('https://www.figma.com' + path, timeout=15, verify=False)
    html = r.text
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)
    app = [s for s in scripts if 'figma_app' in s or 'vendor' in s or 'main' in s]
    print('=== %s -> %d len=%d scripts=%d app_refs=%s' % (path, r.status_code, len(html), len(scripts), app[:3]))
    if app:
        # 保存 HTML
        with open(os.path.join(OUT, 'app_%s.html' % path.strip('/').replace('/', '_')), 'w', encoding='utf-8') as f:
            f.write(html)
        # 下载 app refs
        ctx = ssl.create_default_context()
        for u in app:
            fn = u.split('/')[-1]
            out_js = os.path.join(OUT, fn.replace('.br', ''))
            if os.path.exists(out_js) and os.path.getsize(out_js) > 10000:
                print('  exists:', fn)
                continue
            conn = http.client.HTTPSConnection('www.figma.com', context=ctx, timeout=60)
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
                    print('  DL %s -> %d' % (fn, len(data)))
                except Exception as ex:
                    print('  decode fail %s: %s' % (fn, str(ex)[:40]))
            else:
                print('  DL FAIL %s -> %d' % (fn, resp.status))
        break
