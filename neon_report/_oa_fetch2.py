# -*- coding: utf-8 -*-
"""追 OpenAPI 真实入口"""
import http.client, ssl

ctx = ssl.create_default_context()

def get(host, path, redir=False):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        r = conn.getresponse(); raw = r.read()
        loc = r.getheader('Location')
        st = r.status; conn.close()
        return st, loc, raw
    except Exception as e:
        return 0, None, str(e).encode()

tests = [
    ('api-docs.neon.tech', '/openapi/2.json'),
    ('api-docs.neon.tech', '/openapi/2'),
    ('api.neon.tech', '/openapi.json'),
    ('api.neon.tech', '/v2/openapi.json'),
    ('api.neon.tech', '/openapi'),
    ('api-docs.neon.tech', '/reference/gett-started-with-neon-api'),
    ('neon.com', '/docs/reference/api'),
]
for host, path in tests:
    st, loc, raw = get(host, path)
    print('==', host + path, '->', st, '| loc:', loc, '| len:', len(raw))
    if st == 200:
        print('   head:', raw[:150].decode('utf-8', 'replace').replace('\n', ' '))
