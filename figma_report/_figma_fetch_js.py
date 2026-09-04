# -*- coding: utf-8 -*-
"""下载 Figma 主 bundle JS(从 HAR 拿 URL)并解压 brotli,供静态分析"""
import json, os, re, requests, urllib3, brotli
urllib3.disable_warnings()

HAR = 'C:/Users/tndc2/Desktop/www.figma.com.har'
OUTDIR = 'D:/scan/figma_report/_js/'
os.makedirs(OUTDIR, exist_ok=True)

# 1. 从 HAR 收集 JS 资产 URL
urls = set()
with open(HAR, 'r', encoding='utf-8') as f:
    har = json.load(f)
for e in har['log']['entries']:
    url = e['request']['url']
    if '/webpack-artifacts/assets/' in url and url.endswith('.min.js.br'):
        urls.add(url)

print('js urls:', len(urls))
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Accept-Encoding': 'br'})

# 2. 优先下载主 bundle 和 vendor(大文件),按大小排序
cands = []
for u in urls:
    fn = u.split('/')[-1]
    if 'figma_app' in fn or 'vendor-' in fn or 'react' in fn:
        cands.append(u)
print('candidates:', len(cands))

for u in cands:
    fn = u.split('/')[-1]
    out_br = os.path.join(OUTDIR, fn)
    if os.path.exists(out_br):
        continue
    try:
        r = S.get(u, timeout=60, verify=False)
        if r.status_code == 200 and r.content:
            with open(out_br, 'wb') as f:
                f.write(r.content)
            print('DL %s %d bytes' % (fn, len(r.content)))
        else:
            print('DL FAIL %s -> %d' % (fn, r.status_code))
    except Exception as e:
        print('DL ERR %s -> %s' % (fn, str(e)[:60]))

# 3. 解压所有 .br(保留 .js)
for fn in os.listdir(OUTDIR):
    if not fn.endswith('.br'):
        continue
    js = fn[:-3]
    p_br = os.path.join(OUTDIR, fn)
    p_js = os.path.join(OUTDIR, js)
    if os.path.exists(p_js):
        continue
    try:
        with open(p_br, 'rb') as f:
            data = brotli.decompress(f.read())
        with open(p_js, 'wb') as f:
            f.write(data)
        print('UNBR %s -> %d' % (js, len(data)))
    except Exception as e:
        print('UNBR ERR %s -> %s' % (fn, str(e)[:60]))
