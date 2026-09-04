# -*- coding: utf-8 -*-
"""Netlify:用真实 siteId 测内部端点"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def req(path, method='GET', body=None, headers=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET}
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

tests = [
    ('POST', '/.netlify/functions/database-query', {'siteId': SITE_ID, 'action': 'list'}),
    ('POST', '/.netlify/functions/database-query', {'siteId': SITE_ID, 'action': 'describe'}),
    ('POST', '/.netlify/functions/database-query', {'siteId': SITE_ID, 'action': 'query', 'query': 'select 1'}),
    ('POST', '/.netlify/functions/database-query', {'siteId': SITE_ID, 'action': 'connect', 'connectionString': 'postgres://x'}),
    ('POST', '/.netlify/functions/database-query', {'siteId': SITE_ID}),
    ('GET', '/.netlify/functions/fetch-relevant-installed-extensions-for-site?siteId=%s' % SITE_ID, None),
    ('GET', '/.netlify/functions/fetch-relevant-installed-extensions-for-site?teamId=1643584176', None),
    ('POST', '/.netlify/functions/fetch-extension', {'teamId': '1643584176', 'slug': 'netlify-extension-test'}),
    ('POST', '/.netlify/functions/install-extension', {'teamId': '1643584176', 'slug': 'netlify-extension-test'}),
    ('GET', '/spark-proxy/api/v1/knowledge?scopes=site&siteId=%s' % SITE_ID, None),
    ('GET', '/spark-proxy/api/v1/knowledge?scopes=global', None),
    ('GET', '/spark-proxy/api/prompt-templates?siteId=%s' % SITE_ID, None),
    ('GET', '/.netlify/functions/agent-runner-file-upload?accountId=1643584176', None),
    ('GET', '/api/agent-runners/status', None),
]
for m, p, b in tests:
    try:
        s, raw = req(p, method=m, body=b)
        body = raw[:150].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-8s %-85s %d %s' % (m, p[:85], s, body))
    except Exception as e:
        print('%-8s %-85s ERR %s' % (m, p[:85], str(e)[:40]))
