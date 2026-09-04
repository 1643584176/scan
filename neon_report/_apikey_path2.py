# -*- coding: utf-8 -*-
"""补 key_name 建 API key(带 org_id 变体),然后 Bearer 建项目"""
import http.client, ssl, json, sys, re, html
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'

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

# 建 API key(个人 key)
st, raw = req('POST', '/api_keys', {'key_name': 'sec-pccp-key'})
print('POST /api_keys(key_name) ->', st)
print(raw[:300])
d = json.loads(raw)
key = d.get('key')
print('KEY head:', str(key)[:16], '| full len:', len(str(key)))
if not key:
    sys.exit(1)
open(r'D:\scan\neon_report\_apikey.json', 'w').write(json.dumps({'key': key}))

# Bearer 测试:GET users/me + POST projects(org_id query)
for label, method, path, body in [
    ('GET users/me', 'GET', '/users/me', None),
    ('POST projects q-org', 'POST', '/projects?org_id=%s' % ORG, {'project': {'name': 'sec-apikey-1'}}),
    ('POST projects hdr-org', 'POST', '/projects', {'project': {'name': 'sec-apikey-2'}}),
]:
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    if label == 'POST projects hdr-org':
        h['X-Neon-Org-Id'] = ORG
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    print('\n%s -> %d' % (label, st))
    print(raw[:400])
