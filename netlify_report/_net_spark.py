# -*- coding: utf-8 -*-
"""Netlify:spark-proxy 调用上下文 + bb-api 更多路径"""
import os, re, http.client, ssl, gzip, brotli, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

jsdir = r'D:\scan\netlify_report\_js'
print('===== spark-proxy 调用上下文 =====')
for f in sorted(os.listdir(jsdir)):
    if not f.endswith('.js'):
        continue
    txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'spark-proxy', txt):
        i = m.start()
        ctx = txt[max(0, i - 1500): i + 800]
        # 找 fetch 调用
        for fm in re.finditer(r'fetch\(', ctx):
            j = fm.start()
            seg = ctx[j:j + 300]
            if 'spark' in seg:
                print('[%s]' % f.replace('net_', '').replace('.js', ''))
                print('  fetch:', seg[:250].replace('\n', ' '))
                break
        print('  ctx-pre:', ctx[-200:].replace('\n', ' ')[-160:])
        print()

print('===== bb-api 路径爆破 =====')
ctx = ssl.create_default_context()
def req(path, headers=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=12)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if headers:
        h.update(headers)
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

paths = [
    '/access-control/bb-api/api/v1',
    '/access-control/bb-api/api',
    '/access-control/bb-api/api/v1/builds?site_id=04f08ff6-f274-47ac-b6d7-5fb1e055f3b4',
    '/access-control/bb-api/api/v1/sites/04f08ff6-f274-47ac-b6d7-5fb1e055f3b4/builds',
    '/access-control/bb-api/api/v1/deploys',
    '/access-control/bb-api/api/v1/builds/1',
    '/access-control/bb-api/v1',
    '/access-control/bb-api/api/v1/jobs',
    '/access-control/bb-api/api/v1/site/04f08ff6-f274-47ac-b6d7-5fb1e055f3b4',
    '/access-control/bb-api/api/v1/accounts/1643584176',
    '/access-control/bb-api/api/v1/users/6a979dd2ae93f47d55b62895',
]
for p in paths:
    try:
        s, raw = req(p, headers={'Cookie': COOKIE_NET})
        print('%-70s %d %s' % (p, s, raw[:80].decode('utf-8', 'ignore').replace('\n', ' ')))
    except Exception as e:
        print('%-70s ERR %s' % (p, str(e)[:30]))
