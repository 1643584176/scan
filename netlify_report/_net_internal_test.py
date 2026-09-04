# -*- coding: utf-8 -*-
"""Netlify:内部端点带 cookie 实测(参数猜测)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

ctx = ssl.create_default_context()

def req(path, method='GET', body=None, headers=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = body if isinstance(body, bytes) else json.dumps(body).encode()
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
    ('GET', '/.netlify/functions/fetch-extensions?teamId=1643584176', None),
    ('GET', '/.netlify/functions/fetch-installed-extensions-for-team?teamId=1643584176', None),
    ('GET', '/.netlify/functions/fetch-relevant-installed-extensions-for-site?teamId=1643584176', None),
    ('GET', '/.netlify/functions/extension-proxy?teamId=1643584176', None),
    ('POST', '/.netlify/functions/install-extension?teamId=1643584176', {'slug': 'test'}),
    ('POST', '/.netlify/functions/install-extension', {'teamId': '1643584176', 'slug': 'test'}),
    ('POST', '/.netlify/functions/database-query', {'query': 'select 1', 'readonly': True}),
    ('POST', '/.netlify/functions/database-query?siteId=x', {'query': 'select 1'}),
    ('POST', '/.netlify/functions/fetch-extension?teamId=1643584176', {'slug': 'x'}),
    ('POST', '/.netlify/functions/extension-proxy?teamId=1643584176', {'path': '/', 'method': 'GET'}),
    ('POST', '/.netlify/functions/private-integration-create?teamId=1643584176', {'access_token': 'test'}),
    ('POST', '/.netlify/functions/event-observed', {'event': 'test'}),
    ('POST', '/.netlify/functions/labs-toggle', {'lab': 'test'}),
    ('GET', '/spark-proxy/api/v1/knowledge?scopes=site', None),
    ('GET', '/spark-proxy/api/v1/knowledge?scopes=site&siteId=x', None),
]
for m, p, b in tests:
    try:
        s, raw = req(p, method=m, body=b)
        body = raw[:130].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-8s %-75s %d %s' % (m, p[:75], s, body))
    except Exception as e:
        print('%-8s %-75s ERR %s' % (m, p[:75], str(e)[:40]))
