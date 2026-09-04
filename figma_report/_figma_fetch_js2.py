# -*- coding: utf-8 -*-
"""Figma JS 资产全量下载(http.client,避免 requests 自动解压 br 的坑)"""
import json, os, ssl, http.client, brotli, time

HAR = 'C:/Users/tndc2/Desktop/www.figma.com.har'
OUTDIR = 'D:/scan/figma_report/_js/'
os.makedirs(OUTDIR, exist_ok=True)

with open(HAR, 'r', encoding='utf-8') as f:
    har = json.load(f)
urls = set()
for e in har['log']['entries']:
    url = e['request']['url']
    if '/webpack-artifacts/assets/' in url and (url.endswith('.min.js.br') or url.endswith('.min.css.br') or url.endswith('.min.en.json.br')):
        urls.add(url)
print('urls:', len(urls))

ctx = ssl.create_default_context()
ok, fail = 0, 0
for u in sorted(urls):
    fn = u.split('/')[-1]
    out_js = os.path.join(OUTDIR, fn.replace('.br', ''))
    if os.path.exists(out_js) and os.path.getsize(out_js) > 1000:
        ok += 1
        continue
    path = '/webpack-artifacts/assets/' + fn
    try:
        conn = http.client.HTTPSConnection('www.figma.com', context=ctx, timeout=30)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                           'Accept-Encoding': 'br, gzip, deflate'})
        r = conn.getresponse()
        body = r.read()
        conn.close()
        if r.status != 200 or not body:
            print('FAIL %s -> %d' % (fn, r.status))
            fail += 1
            continue
        enc = r.getheader('Content-Encoding', '')
        if 'br' in enc:
            try:
                data = brotli.decompress(body)
            except Exception as e:
                print('BRFAIL %s -> %s' % (fn, str(e)[:40]))
                fail += 1
                continue
        else:
            data = body
        with open(out_js, 'wb') as f:
            f.write(data)
        print('OK %s -> %d bytes' % (fn.replace('.br', ''), len(data)))
        ok += 1
    except Exception as e:
        print('ERR %s -> %s' % (fn, str(e)[:60]))
        fail += 1
    time.sleep(0.15)
print('done: ok=%d fail=%d' % (ok, fail))
