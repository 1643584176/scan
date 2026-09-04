# -*- coding: utf-8 -*-
"""Netlify:调用函数探测结果"""
import http.client, ssl, gzip, brotli, json

ctx = ssl.create_default_context()

def get(host, path):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=60)
    conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip'})
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

st, raw = get('sec-test-rcf6lz.netlify.app', '/.netlify/functions/probe1')
print('status:', st)
txt = raw.decode('utf-8', 'ignore')
print('len:', len(txt))
try:
    d = json.loads(txt)
    print(json.dumps(d, indent=1, ensure_ascii=False)[:3000])
except Exception:
    print(txt[:2000])
