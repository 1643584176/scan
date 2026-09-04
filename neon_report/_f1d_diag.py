# -*- coding: utf-8 -*-
"""1) presign 恢复探测 2) function/storage/proxy 域名 DNS 对比 3) 403 响应头全量"""
import http.client, ssl, json, socket, sys
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

# 1. presign 恢复
def req(method, path, body=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
    return st, raw

st, raw = req('POST', '/projects/%s/branches/%s/buckets' % (P, B), {'name': 'kp1'})
print('create kp1 -> %d' % st)
if st in (200, 201):
    st2, raw2 = req('POST', '%s/projects/%s/branches/%s/buckets/kp1/objects/o1.txt/presign' % (API_BASE, P, B),
                    {'operation': 'upload', 'content_type': 'text/plain'})
    print('presign kp1 -> %d | %s' % (st2, raw2.decode(errors='replace')[:120]))
    req('DELETE', '/projects/%s/branches/%s/buckets/kp1' % (P, B))
    print('cleaned kp1')

# 2. DNS 对比
for host in ('br-wandering-field-w2ob6mpn-kf1.compute.c-1.us-east-2.aws.neon.build',
             'br-wandering-field-w2ob6mpn.storage.c-1.us-east-2.aws.neon.build',
             'console-stage.neon.build',
             'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'):
    try:
        ips = sorted(set(a[4][0] for a in socket.getaddrinfo(host, 443)))
        print('DNS %s -> %s' % (host, ips))
    except Exception as e:
        print('DNS %s -> ERR %s' % (host, e))

# 3. function 域 403 响应全头
c = http.client.HTTPSConnection('br-wandering-field-w2ob6mpn-kf1.compute.c-1.us-east-2.aws.neon.build', context=ctx, timeout=25)
c.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
r = c.getresponse(); raw = r.read(); c.close()
print('function 403 full headers:', dict(r.getheaders()))
