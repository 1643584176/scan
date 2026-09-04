# -*- coding: utf-8 -*-
"""bucket 名候选迭代 + access_level 显式"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

def req(method, path, body=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
    return st, raw[:500]

cands = [
    {'name': 'kb1'},
    {'name': 'k-b1'},
    {'name': 'k-probe-bucket-2026'},
    {'name': 'kb1', 'access_level': 'private'},
    {'name': 'K-B1'},
    {'name': 'a' * 20},
]
for body in cands:
    st, raw = req('POST', '/projects/%s/branches/%s/buckets' % (P, B), body)
    print('create %-28s -> %d | %s' % (body, st, raw.decode(errors='replace')[:220]))
    if st in (200, 201):
        # 清理
        name = body['name']
        st2, _ = req('DELETE', '/projects/%s/branches/%s/buckets/%s' % (P, B, name))
        print('   cleanup -> %d' % st2)
        break
