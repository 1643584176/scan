# -*- coding: utf-8 -*-
"""Netlify:内部端点未授权访问探测(匿名 vs 认证对比)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET, AUTH_HEADER

ctx = ssl.create_default_context()

def req(host, path, method='GET', headers=None, body=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

# 匿名 vs 认证 对比(app.netlify.com 上的内部端点)
endpoints = [
    ('GET', '/.netlify/functions/labs-list'),
    ('GET', '/.netlify/functions/fetch-integration-hub'),
    ('GET', '/.netlify/functions/generate-bandwidth-usage-csv'),
    ('GET', '/.netlify/functions/git'),
    ('GET', '/.netlify/functions/hubspot'),
    ('GET', '/.netlify/functions/workflow-ui'),
    ('GET', '/.netlify/functions/handler/on-disable'),
    ('GET', '/.netlify/functions/verify?domain=example.com'),
    ('GET', '/.netlify/functions/fetch-build-plugins'),
    ('GET', '/.netlify/functions/fetch-extensions'),
    ('GET', '/.netlify/functions/manage-extension-proxy'),
    ('GET', '/.netlify/builders/versions'),
    ('GET', '/.netlify/builders/notifications'),
    ('GET', '/.netlify/identity'),
    ('GET', '/.netlify/large-media'),
    ('GET', '/.netlify/images'),
    ('POST', '/.netlify/functions/labs-toggle'),
    ('POST', '/.netlify/functions/database-query'),
    ('POST', '/.netlify/functions/extension-proxy'),
    ('POST', '/.netlify/functions/fetch-extension'),
    ('POST', '/.netlify/functions/install-extension'),
    ('POST', '/.netlify/functions/event-observed'),
    ('POST', '/.netlify/functions/contact-sales'),
    ('POST', '/.netlify/functions/support-tickets'),
    ('POST', '/.netlify/functions/validate-address'),
    ('GET', '/api/deploy-diagnostics'),
    ('GET', '/api/experiments'),
    ('GET', '/api/agent-runners/status'),
    ('GET', '/spark-proxy/api/prompt-templates'),
    ('GET', '/spark-proxy/api/v1/knowledge?scopes=site'),
]

print('%-8s %-55s %-6s %-6s %s' % ('method', 'path', 'anon', 'auth', 'anon body'))
for m, p in endpoints:
    try:
        s1, b1 = req('app.netlify.com', p, method=m)
        s2, b2 = req('app.netlify.com', p, method=m, headers={'Cookie': COOKIE_NET})
        body1 = b1[:60].decode('utf-8', 'ignore').replace('\n', ' ')
        flag = ' ***' if (s1 == 200 and s2 == 401) or (s1 == 200 and len(b1) > 50 and s2 != 200) else ''
        print('%-8s %-55s %-6s %-6s %s%s' % (m, p[:55], s1, s2, body1, flag))
    except Exception as e:
        print('%-8s %-55s ERR %s' % (m, p[:55], str(e)[:40]))
