# -*- coding: utf-8 -*-
"""capability 面: dev_servers / ai-gateway 完整 / service instances"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=30):
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

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-56s %s | %s' % (tag, st, b[:300].replace('\n', ' ')))
    return st, b

print('== 1. ai-gateway providers 完整 JSON ==')
st, b = req('GET', '/api/v1/ai-gateway/providers', None, None)
try:
    d = json.loads(b)
    print('keys:', list(d.keys()))
    print(json.dumps(d, indent=1)[:1800])
except Exception as e:
    print('raw:', b[:500])

print()
print('== 2. dev_servers 创建 ==')
for body in [
    {'site_id': SITE_A},
    {'branch': 'main'},
    {'name': 'zz-ds'},
]:
    st, b = probe('POST dev_servers %s' % list(body.keys()), 'POST',
                  '/api/v1/sites/%s/dev_servers' % SITE_A, body)
    if st in (200, 201, 202):
        print('  !! created:', b[:300])
        break
probe('GET dev_servers', 'GET', '/api/v1/sites/%s/dev_servers' % SITE_A)

print()
print('== 3. service instances 创建 ==')
for body in [{}, {'service_slug': 'astra'}, {'slug': 'astra'}]:
    st, b = probe('POST service-instances %s' % list(body.keys()), 'POST',
                  '/api/v1/sites/%s/service-instances' % SITE_A, body)
    if st in (200, 201, 202):
        print('  !! created:', b[:300])
        break
probe('GET service-instances', 'GET', '/api/v1/sites/%s/service-instances' % SITE_A)
print('done')
