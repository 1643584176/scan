# -*- coding: utf-8 -*-
"""Netlify:GitHub 公开搜索 siteId(用于越权验证)"""
import http.client, ssl, gzip, brotli, sys, json

ctx = ssl.create_default_context()

def get(host, path, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (sec-test)', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/vnd.github+json'}
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

# GitHub code search(无需认证,限速)
for q in ['NETLIFY_SITE_ID path:.env', 'netlify site_id in:file', 'site_id netlify.toml']:
    import urllib.parse
    path = '/search/code?q=' + urllib.parse.quote(q)
    s, raw = get('api.github.com', path)
    print(q, '->', s, raw[:200].decode('utf-8', 'ignore'))
    if s == 200:
        d = json.loads(raw)
        for item in d.get('items', [])[:3]:
            print('  ', item.get('repository', {}).get('full_name'), item.get('path'))
    break
