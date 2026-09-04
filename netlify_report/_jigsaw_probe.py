# -*- coding: utf-8 -*-
"""jigsaw 服务路径指纹 + identeer-proxy providers"""
import socket, http.client, ssl

ctx = ssl.create_default_context()

def probe(host, path, port=443):
    try:
        conn = http.client.HTTPSConnection(host, port, context=ctx, timeout=10)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        r = conn.getresponse()
        raw = r.read(150)
        st = r.status
        ct = r.getheader('Content-Type', '')
        conn.close()
        return st, ct, raw.decode('utf-8', 'replace').replace('\n', ' ')
    except Exception as e:
        return 'ERR', '', str(e)[:50]

print('--- jigsaw.services-prod.nsvcs.net ---')
for p in ['/', '/healthz', '/health', '/ready', '/status', '/version', '/info', '/api', '/v1', '/graphql', '/metrics', '/ping', '/internal', '/.well-known/netlify']:
    st, ct, b = probe('jigsaw.services-prod.nsvcs.net', p)
    if st not in (404,):
        print('%-24s %s %s %s' % (p, st, ct, b[:80]))
print()

print('--- identeer providers via app proxy ---')
import gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B
conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=15)
h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
     'Accept': 'application/json', 'Cookie': COOKIE_B}
conn.request('GET', '/.netlify/functions/identeer-proxy/providers', headers=h)
r = conn.getresponse()
raw = r.read()
enc = r.getheader('Content-Encoding')
if enc == 'br':
    raw = brotli.decompress(raw)
elif enc == 'gzip':
    raw = gzip.decompress(raw)
print('identeer providers:', r.status, raw[:400].decode('utf-8', 'replace'))
conn.close()
