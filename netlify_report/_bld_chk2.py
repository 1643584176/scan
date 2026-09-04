# -*- coding: utf-8 -*-
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
ctx = ssl.create_default_context()
NF_TOKEN = '062d3d30-a9b9-4477-aa69-4a3dba0d5b30'

def api(host, path, token, method='GET', body=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    payload = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=payload, headers=h)
    r = conn.getresponse(); raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status; conn.close(); return st, raw

print('=== NETLIFY_FUNCTIONS_TOKEN 平台 API ===')
for path in ['/api/v1/user', '/api/v1/sites?per_page=50', '/api/v1/accounts']:
    try:
        st, raw = api('api.netlify.com', path, NF_TOKEN)
        print('GET %s -> %d %s' % (path, st, raw[:300].decode('utf-8', 'replace').replace(chr(10), ' ')))
    except Exception as e:
        print('GET %s ERR %s' % (path, str(e)[:120]))

print()
print('=== B 账号 user 详情(git 能力)===')
from _net_creds import TOKEN_B
for path in ['/api/v1/user', '/api/v1/accounts?per_page=20']:
    try:
        st, raw = api('api.netlify.com', path, TOKEN_B)
        print('GET %s -> %d' % (path, st))
        if st == 200:
            print(raw[:2000].decode('utf-8', 'replace'))
    except Exception as e:
        print('GET %s ERR %s' % (path, str(e)[:120]))
