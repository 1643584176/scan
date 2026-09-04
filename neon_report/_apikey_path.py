# -*- coding: utf-8 -*-
"""走 API key 路径:POST /api_keys -> 用 Bearer 测 createProject"""
import http.client, ssl, json, sys, re, html
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'

# csrf
conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
r = conn.getresponse(); body = r.read(); conn.close()
csrf_meta = html.unescape(re.search(r'<meta name="csrf-token" content="([^"]+)"', body.decode('utf-8', 'replace')).group(1))

def req(method, path, body=None, extra=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Cookie': cookie_str(), 'X-CSRF-Token': csrf_meta}
    h.update(HEADERS_TEST)
    if extra: h.update(extra)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

# 1. 建 API key
st, raw = req('POST', '/api_keys', {'name': 'sec-pccp-key'})
print('POST /api_keys ->', st)
print(raw[:400])
try:
    d = json.loads(raw)
    key = d.get('key') or (d.get('api_key') or {}).get('key')
    kid = d.get('id')
    print('KEY:', str(key)[:20], '... id:', kid)
except Exception as e:
    print('parse err', e); sys.exit(1)

if key:
    open(r'D:\scan\neon_report\_apikey.json', 'w').write(json.dumps({'key': key, 'id': kid}))
    # 2. Bearer + query org_id 建项目
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request('POST', API_BASE + '/projects?org_id=%s' % ORG,
                 body=json.dumps({'project': {'name': 'sec-apikey-1'}}).encode(), headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    print('\nBearer POST /projects?org_id ->', st)
    print(raw[:500])
