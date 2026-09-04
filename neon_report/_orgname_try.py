# -*- coding: utf-8 -*-
"""query 参数名矩阵:org_id / orgId / organization_id / org"""
import http.client, ssl, json, sys
ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

def post(qs):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request('POST', API_BASE + '/projects' + qs,
                 body=json.dumps({'project': {'name': 'sec-q-1'}}).encode(), headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:130]

for name in ['org_id', 'orgId', 'organization_id', 'org', 'organizationId']:
    st, raw = post('?%s=%s' % (name, ORG))
    print('%-20s -> %d %s' % (name, st, raw))
