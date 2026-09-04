# -*- coding: utf-8 -*-
"""清理遗留配置 + 确认 data-api 终态"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

# cors 还原尝试:空串
for val in ['', 'http://localhost']:
    st, raw = req('PATCH', '/projects/%s/branches/%s/data-api/neondb' % (P, B),
                  {'settings': {'server_cors_allowed_origins': val}})
    print('PATCH cors=%r -> %d | %s' % (val, st, raw[:150].decode(errors='replace')), flush=True)
    if st == 201:
        break
    time.sleep(1)

st, raw = req('GET', '/projects/%s/branches/%s/data-api/neondb' % (P, B))
print('\nfinal data-api:', raw[:600].decode(errors='replace'), flush=True)

# jwks/auth 终态确认
st, raw = req('GET', '/projects/%s/jwks' % P)
print('\njwks:', raw[:200].decode(errors='replace'), flush=True)
