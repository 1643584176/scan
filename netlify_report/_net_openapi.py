# -*- coding: utf-8 -*-
"""Netlify:尝试获取公开 OpenAPI 规范"""
import http.client, ssl, gzip, brotli

ctx = ssl.create_default_context()

def get(host, path):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
    conn.request('GET', path, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
        'Accept': 'application/json, application/yaml, text/plain, */*',
        'Accept-Encoding': 'br, gzip'})
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    ct = r.getheader('Content-Type', '')
    conn.close()
    return st, ct, raw

for host, p in [
    ('api.netlify.com', '/openapi.json'),
    ('api.netlify.com', '/openapi.yaml'),
    ('api.netlify.com', '/api/v1/openapi.json'),
    ('api.netlify.com', '/.well-known/openapi.json'),
    ('docs.netlify.com', '/api/openapi.json'),
    ('docs.netlify.com', '/api/_openapi.json'),
    ('www.netlify.com', '/docs/api/openapi.json'),
]:
    try:
        s, ct, raw = get(host, p)
        print('%s%s -> %d %s len=%d' % (host, p, s, ct[:40], len(raw)))
        if s == 200 and len(raw) > 1000:
            open(r'D:\scan\netlify_report\_js\net_openapi.json', 'wb').write(raw)
            print('  SAVED net_openapi.json')
            break
    except Exception as e:
        print('%s%s ERR %s' % (host, p, str(e)[:60]))
