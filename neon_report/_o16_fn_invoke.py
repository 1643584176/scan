# -*- coding: utf-8 -*-
"""invocation_url 403 排查:请求变体矩阵"""
import http.client, ssl

ctx = ssl.create_default_context()
HOST = 'br-wandering-field-w2ob6mpn-secfn22529870.compute.c-1.us-east-2.aws.neon.build'

def call(path='/', method='GET', headers=None, port=443):
    try:
        conn = http.client.HTTPSConnection(HOST, port, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0'}
        if headers:
            h.update(headers)
        conn.request(method, path, headers=h)
        r = conn.getresponse()
        data = r.read().decode('utf-8', 'replace')
        st = r.status
        conn.close()
        return st, data[:400].replace('\n', ' ')
    except Exception as e:
        return -1, 'EXC %s' % e

tests = [
    ('default', {}, 'GET', '/'),
    ('x-bb', {'X-Bug-Bounty': 'xxbo'}, 'GET', '/'),
    ('curl-ua', {'User-Agent': 'curl/8.5.0'}, 'GET', '/'),
    ('chrome-ua', {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'}, 'GET', '/'),
    ('accept-all', {'Accept': '*/*'}, 'GET', '/'),
    ('post', {}, 'POST', '/'),
    ('head', {}, 'HEAD', '/'),
    ('path-x', {}, 'GET', '/x'),
    ('options', {'Origin': 'http://localhost:3000'}, 'OPTIONS', '/'),
    ('no-ua', {'User-Agent': ''}, 'GET', '/'),
    ('x-neon', {'X-Neon-Project-Id': 'orange-sun-90493739'}, 'GET', '/'),
]
for name, hdrs, m, p in tests:
    st, raw = call(p, m, hdrs)
    print('[%s] %d %s' % (name, st, raw), flush=True)
