# -*- coding: utf-8 -*-
"""Netlify:endpoint-map 站点分析 + GitHub 源查找"""
import http.client, ssl, sys, re

ctx = ssl.create_default_context()

def get(host, path, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': '*/*'}
    if headers:
        h.update(headers)
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        import brotli
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        import gzip
        raw = gzip.decompress(raw)
    st = r.status
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    conn.close()
    return st, raw, hdrs

# 1. 首页(带 UA 浏览器头)
s, raw, hdrs = get('hackerone-endpoint-map.netlify.app', '/',
                   headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'})
print('index:', s, hdrs.get('content-type'), len(raw))
txt = raw.decode('utf-8', 'ignore')
# 找 js bundle / 链接
for m in re.findall(r'(?:src|href)="([^"]+)"', txt)[:20]:
    print('  asset:', m)
open(r'D:\scan\netlify_report\endpoint-map-index.html', 'w', encoding='utf-8').write(txt)

# 2. 常见 GitHub 源尝试
for repo in ['netlify/endpoint-map', 'netlify/hackathon-assets', 'netlify/hackerone-endpoint-map',
             'netlify/open-api', 'netlify/security-hackathon']:
    s, raw, hdrs = get('api.github.com', '/repos/%s' % repo,
                       headers={'User-Agent': 'Mozilla/5.0 (sec)'})
    print(repo, '->', s)
    if s == 200:
        import json
        d = json.loads(raw)
        print('  default_branch:', d.get('default_branch'), 'desc:', str(d.get('description'))[:80])
