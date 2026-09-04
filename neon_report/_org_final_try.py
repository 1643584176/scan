# -*- coding: utf-8 -*-
"""最后组合:body 内嵌 org_id / 路径变体 / header 变体"""
import http.client, ssl, json, sys
ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def req(method, path, body=None, hdr=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    if hdr: h.update(hdr)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:140]

# 1. body project 内 org_id
print('1:', req('POST', '/projects', {'project': {'name': 'sec-i-1', 'org_id': ORG}}))
# 2. 路径变体
print('2:', req('POST', '/organizations/%s/projects' % ORG, {'project': {'name': 'sec-i-2'}}))
# 3. header 变体
for hn in ['X-Organization-Id', 'Neon-Organization', 'X-Neon-Organization', 'X-Org-Id', 'Organization-Id']:
    st, raw = req('POST', '/projects', {'project': {'name': 'sec-i-3'}}, {hn: ORG})
    print('3 hdr %-22s -> %d %s' % (hn, st, raw))
# 4. query 组合 org_id + body organization
st, raw = req('POST', '/projects?org_id=%s' % ORG, {'project': {'name': 'sec-i-4'}, 'organization_id': ORG})
print('4:', st, raw)
