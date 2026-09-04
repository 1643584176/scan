# -*- coding: utf-8 -*-
"""Netlify:agent-runner upload 端点 host 与鉴权矩阵"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, TOKEN_A
ctx = ssl.create_default_context()

ACC_UUID = '6a979dd2ae93f47d55b62897'

def req(host, path, method='POST', raw=None, headers=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Origin': 'https://app.netlify.com'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=raw, headers=h)
    r = conn.getresponse(); raw2 = r.read()
    st = r.status; conn.close()
    return st, raw2[:300].decode('utf-8', 'replace')

fname = 'ar-test-%d.txt' % int(time.time())
content = b'netlify ar test file\n'
qs = 'accountId=%s&filename=%s' % (ACC_UUID, fname)

for host in ['app.netlify.com', 'api.netlify.com']:
    s, b = req(host, '/api/agent-runner-file-upload?' + qs, raw=content,
               headers={'Content-Type': 'text/plain'})
    print('%-20s upload -> %d %s' % (host, s, b[:200]))

# status 端点对照
for host in ['app.netlify.com', 'api.netlify.com']:
    s, b = req(host, '/api/agent-runners/status', method='GET')
    print('%-20s status GET -> %d %s' % (host, s, b[:200]))
