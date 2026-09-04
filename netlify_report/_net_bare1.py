# -*- coding: utf-8 -*-
"""裸 id 端点第一轮: 列自己的 deploy/agent-runner 真实 id, 跨账号打 deploy_id 族"""
import http.client, ssl, gzip, brotli, json, sys, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if body is not None else None
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

print('== 1. 列 A 站 deploys ==')
st, b = req('GET', '/api/v1/sites/%s/deploys?per_page=5' % SITE_A, token=TOKEN_A)
print(st, b[:600])

print()
print('== 2. 列 agent_runners(A/B)==')
for tok, tag in [(TOKEN_A, 'A'), (TOKEN_B, 'B')]:
    st, b = req('GET', '/agent_runners', token=tok)
    print(tag, st, b[:400])
