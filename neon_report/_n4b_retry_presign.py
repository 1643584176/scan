# -*- coding: utf-8 -*-
"""presign 服务恢复探测(单一请求)+ credentials schema 名查找"""
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
    return st, raw

# 1. 建临时 bucket 测 presign
st, raw = req('POST', '/projects/%s/branches/%s/buckets' % (P, B), {'name': 'kp0'})
print('create kp0 -> %d | %s' % (st, raw.decode(errors='replace')[:120]))
if st in (200, 201):
    st2, raw2 = req('POST', '%s/projects/%s/branches/%s/buckets/kp0/objects/o1.txt/presign' % (API_BASE, P, B),
                    {'operation': 'upload', 'content_type': 'text/plain'})
    print('presign kp0 -> %d | %s' % (st2, raw2.decode(errors='replace')[:150]))
    st3, _ = req('DELETE', '/projects/%s/branches/%s/buckets/kp0' % (P, B))
    print('clean kp0 -> %d' % st3)

# 2. credentials 相关 schema 名
d = json.load(open(r'D:\scan\neon_report\_openapi_v2.json'))
names = [k for k in d['components']['schemas'] if 'redential' in k or 'oken' in k]
print('credential schemas:', names)
