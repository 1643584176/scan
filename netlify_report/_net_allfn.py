# -*- coding: utf-8 -*-
"""Netlify:全部内部函数端点 匿名 vs 认证 对比(补全清单)"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def req(path, method='GET', body=None, headers=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
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

endpoints = [
    ('GET', '/.netlify/functions/get-trial-info'),
    ('GET', '/.netlify/functions/get-payment-customer'),
    ('GET', '/.netlify/functions/get-team-plan'),
    ('GET', '/.netlify/functions/fetch-site'),
    ('GET', '/.netlify/functions/get-sites'),
    ('GET', '/.netlify/functions/git-connect'),
    ('GET', '/.netlify/functions/start-new-site'),
    ('GET', '/.netlify/functions/build-context'),
    ('GET', '/.netlify/functions/generate-signed-url'),
    ('GET', '/.netlify/functions/validate-signed-url'),
    ('GET', '/.netlify/functions/get-extension-config'),
    ('GET', '/.netlify/functions/get-extension-marketplace'),
    ('GET', '/.netlify/functions/get-extensions-installed'),
    ('GET', '/.netlify/functions/extension-details'),
    ('GET', '/.netlify/functions/integration-details'),
    ('GET', '/.netlify/functions/fetch-integration'),
    ('GET', '/.netlify/functions/fetch-private-integrations'),
    ('GET', '/.netlify/functions/fetch-integration-hub'),
    ('GET', '/.netlify/functions/get-integration-config'),
    ('GET', '/.netlify/functions/fetch-databases'),
    ('GET', '/.netlify/functions/fetch-database-schemas'),
    ('GET', '/.netlify/functions/fetch-database-connection'),
    ('GET', '/.netlify/functions/graphql'),
    ('GET', '/.netlify/functions/me'),
    ('GET', '/.netlify/functions/csrf'),
    ('GET', '/.netlify/functions/auth'),
    ('GET', '/.netlify/functions/logout'),
    ('GET', '/.netlify/functions/token'),
    ('GET', '/.netlify/functions/github'),
    ('GET', '/.netlify/functions/github-callback'),
    ('GET', '/.netlify/functions/token-exchange'),
    ('POST', '/.netlify/functions/get-trial-info'),
    ('POST', '/.netlify/functions/get-payment-customer'),
    ('POST', '/.netlify/functions/fetch-databases'),
    ('POST', '/.netlify/functions/fetch-database-schemas'),
    ('POST', '/.netlify/functions/fetch-database-connection'),
    ('POST', '/.netlify/functions/get-extension-config'),
    ('POST', '/.netlify/functions/extension-details'),
    ('POST', '/.netlify/functions/fetch-integration'),
    ('POST', '/.netlify/functions/fetch-private-integrations'),
    ('POST', '/.netlify/functions/fetch-site'),
    ('POST', '/.netlify/functions/get-sites'),
    ('POST', '/.netlify/functions/generate-signed-url'),
    ('POST', '/.netlify/functions/validate-signed-url'),
    ('GET', '/api/v2/user'),
    ('GET', '/api/v2/sites'),
    ('GET', '/api/v2/accounts'),
    ('GET', '/api/experiments'),
    ('GET', '/api/agent-runners'),
    ('GET', '/api/agent-runners/%s' % 'x'),
]
print('%-8s %-58s %-6s %-6s %s' % ('method', 'path', 'anon', 'auth', 'auth body'))
for m, p in endpoints:
    try:
        s1, b1 = req(p, method=m)
        s2, b2 = req(p, method=m, headers={'Cookie': COOKIE_NET})
        body2 = b2[:70].decode('utf-8', 'ignore').replace('\n', ' ')
        flag = ' ***' if (s1 == 200 and s2 != 200 and len(b1) > 10) else ''
        print('%-8s %-58s %-6s %-6s %s%s' % (m, p[:58], s1, s2, body2, flag))
    except Exception as e:
        print('%-8s %-58s ERR %s' % (m, p[:58], str(e)[:40]))
