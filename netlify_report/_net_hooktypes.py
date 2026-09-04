# -*- coding: utf-8 -*-
"""dump 完整 hooks/types + GET/POST /hooks?site_id= 变体"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

st, b = req('GET', '/api/v1/hooks/types')
d = json.loads(b)
print('hook types count:', len(d))
for t in d:
    evs = t.get('events', [])
    fs = [(f['name'], f.get('options', {}).get('title', '')) for f in t.get('fields', [])]
    print('- type=%s events=%s' % (t.get('type'), evs))
    for n, ti in fs:
        print('    field: %s (%s)' % (n, ti))

print()
print('== GET /hooks 变体 ==')
for q in ['', '?site_id=%s' % SITE_A, '?site_slug=1643584176']:
    st, b = req('GET', '/api/v1/hooks%s' % q)
    print('GET /hooks%s -> %s | %s' % (q, st, b[:200].replace('\n', ' ')))

print()
print('== POST /hooks?site_id= ==')
for body in [
    {'type': 'url', 'event': 'deploy_succeeded', 'url': 'https://example.com/zz'},
]:
    st, b = req('POST', '/api/v1/hooks?site_id=%s' % SITE_A, body)
    print('POST /hooks?site_id -> %s | %s' % (st, b[:300].replace('\n', ' ')))
