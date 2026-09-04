# -*- coding: utf-8 -*-
"""Buckets 故障边界诊断:逐个端点测,画出 presign 404 的故障范围"""
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

def show(tag, r):
    st, raw = r
    print('[%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:220]))

# 1. list buckets(基线:kb1/kb2/kb3 应都在)
show('list buckets', req('GET', '/projects/%s/branches/%s/buckets' % (P, B)))

# 2. list objects 路由
show('list objects kb1', req('GET', '/projects/%s/branches/%s/buckets/kb1/objects' % (P, B)))

# 3. session download 路由(对象不存在 vs route 404 文案区分)
show('session dl o1.txt', req('GET', '/projects/%s/branches/%s/buckets/kb1/objects/o1.txt/download' % (P, B)))

# 4. presign upload 已知挂
show('presign up kb1', req('POST', '%s/projects/%s/branches/%s/buckets/kb1/objects/o1.txt/presign' % (API_BASE, P, B),
                           {'operation': 'upload', 'content_type': 'text/plain'}))

# 5. presign download 是否也挂
show('presign dl kb1', req('POST', '%s/projects/%s/branches/%s/buckets/kb1/objects/o1.txt/presign' % (API_BASE, P, B),
                           {'operation': 'download'}))

# 6. public_read bucket 是否走不同路径
show('create kb4 public', req('POST', '/projects/%s/branches/%s/buckets' % (P, B),
                              {'name': 'kb4', 'access_level': 'public_read'}))
show('presign up kb4', req('POST', '%s/projects/%s/branches/%s/buckets/kb4/objects/o1.txt/presign' % (API_BASE, P, B),
                           {'operation': 'upload', 'content_type': 'text/plain'}))

# 7. bucket delete 路由是否正常(清 kb4 探 delete 路由)
show('delete kb4', req('DELETE', '/projects/%s/branches/%s/buckets/kb4' % (P, B)))
