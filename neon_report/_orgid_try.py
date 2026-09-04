# -*- coding: utf-8 -*-
"""org_id 传递位置矩阵:body / header / query"""
import http.client, ssl, json, sys, re, html
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'

# 拿 meta csrf
conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
r = conn.getresponse(); body = r.read(); conn.close()
txt = body.decode('utf-8', 'replace')
csrf_meta = html.unescape(re.search(r'<meta name="csrf-token" content="([^"]+)"', txt).group(1))

def post(label, path, body, hdr=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Cookie': cookie_str(), 'X-CSRF-Token': csrf_meta}
    h.update(HEADERS_TEST)
    if hdr: h.update(hdr)
    conn.request('POST', API_BASE + path, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    print('%-34s -> %d %s' % (label, st, raw[:160]))

base = {'project': {'name': 'sec-var-1'}}
# 1. query(已试,对照)
post('query only', '/projects?org_id=%s' % ORG, base)
# 2. body 顶层 org_id
b2 = dict(base); b2['org_id'] = ORG
post('body org_id', '/projects', b2)
# 3. header X-Neon-Org-Id + query
post('hdr X-Neon-Org-Id', '/projects?org_id=%s' % ORG, base, {'X-Neon-Org-Id': ORG})
# 4. body org_id + query 都有
b4 = dict(base); b4['org_id'] = ORG
post('both', '/projects?org_id=%s' % ORG, b4)
