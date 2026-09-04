# -*- coding: utf-8 -*-
"""presign upload 调试:输出 URL 供 curl 测试 + 探测 storage host 行为"""
import http.client, ssl, json, sys, urllib.parse
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

def req(method, path, body=None, hdrs=None, host=None, auth=True):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    if auth:
        h['Authorization'] = 'Bearer ' + key
    if body is not None and not isinstance(body, (bytes, str)):
        h['Content-Type'] = 'application/json'
    h.update(hdrs or {})
    conn = http.client.HTTPSConnection(host or API_HOST, context=ctx, timeout=25)
    payload = None
    if isinstance(body, bytes):
        payload = body
    elif isinstance(body, str):
        payload = body.encode()
    elif body is not None:
        payload = json.dumps(body).encode()
    conn.request(method, path, body=payload, headers=h)
    r = conn.getresponse(); raw = r.read()
    hdrs_r = {k.lower(): v for k, v in r.getheaders()}
    st = r.status; conn.close()
    return st, raw, hdrs_r

# 1. storage host 根(探测边缘行为)
st, raw, h0 = req('GET', '/', host='br-wandering-field-w2ob6mpn.storage.c-1.us-east-2.aws.neon.build', auth=False)
print('storage root GET ->', st, '| server:', h0.get('server'), '| len:', len(raw))
print('  body:', raw[:200])

# 2. 建 bucket + presign upload
st, raw, _ = req('POST', '/projects/%s/branches/%s/buckets' % (P, B), {'name': 'kb1'})
print('create bucket ->', st)
st, raw, _ = req('POST', '%s/projects/%s/branches/%s/buckets/kb1/objects/o1.txt/presign' % (API_BASE, P, B),
                 {'operation': 'upload', 'content_type': 'text/plain'})
pr = json.loads(raw)
print('PRESIGN_URL=%s' % pr['url'])
print('PRESIGN_HEADERS=%s' % json.dumps(pr.get('headers', {})))

# 3. python 直接 PUT(打印响应头)
u = urllib.parse.urlparse(pr['url'])
st2, raw2, h2 = req('PUT', u.path + '?' + u.query, 'K_BUCKET_PROBE_1',
                    {'Content-Type': 'text/plain'}, host=u.netloc, auth=False)
print('python PUT ->', st2, '| headers:', {k: v for k, v in h2.items() if k in ('server', 'x-amz-request-id', 'content-type')})
print('  body:', raw2[:300])

# 4. 不带 content-type 的 presign + PUT(0字节)
st, raw, _ = req('POST', '%s/projects/%s/branches/%s/buckets/kb1/objects/empty.bin/presign' % (API_BASE, P, B),
                 {'operation': 'upload'})
pr2 = json.loads(raw)
u2 = urllib.parse.urlparse(pr2['url'])
st3, raw3, h3 = req('PUT', u2.path + '?' + u2.query, '', {}, host=u2.netloc, auth=False)
print('PUT empty no-ct ->', st3, '| body:', raw3[:200])
