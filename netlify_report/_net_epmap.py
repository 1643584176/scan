# -*- coding: utf-8 -*-
"""Netlify:抓官方端点地图 PNG + endpoint-map 站点"""
import http.client, ssl, sys

ctx = ssl.create_default_context()

def get(host, path, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip'}
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

# 1. endpoint-map.png
s, raw, hdrs = get('hackerone-endpoint-map.netlify.app', '/endpoint-map.png')
print('endpoint-map.png:', s, hdrs.get('content-type'), len(raw))
if s == 200 and len(raw) > 1000:
    open(r'D:\scan\netlify_report\endpoint-map.png', 'wb').write(raw)
    print('saved')

# 2. 站点首页(可能列出更多子域/资源)
s, raw, hdrs = get('hackerone-endpoint-map.netlify.app', '/')
print('index:', s, hdrs.get('content-type'), len(raw))
if s == 200:
    txt = raw.decode('utf-8', 'ignore')
    open(r'D:\scan\netlify_report\endpoint-map-index.html', 'w', encoding='utf-8').write(txt)
    # 提取链接/子域
    import re
    for m in sorted(set(re.findall(r'[a-zA-Z0-9*_.-]+\.netlify[a-zA-Z0-9./_-]*', txt)))[:40]:
        print('  sub:', m)
    for m in sorted(set(re.findall(r'[a-zA-Z0-9-]+\.(?:com|app|dev|io)[a-zA-Z0-9./_-]*', txt)))[:40]:
        if 'netlify' not in m:
            print('  dom:', m)
