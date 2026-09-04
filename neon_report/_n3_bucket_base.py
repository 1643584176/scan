# -*- coding: utf-8 -*-
"""Buckets 阶段1:创建/上传/下载/分支继承隔离语义
全部自建资源,结束全清。零破坏。"""
import http.client, ssl, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']

P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
BUCKET = 'kb1'
OBJ = 'o1.txt'

def req(method, path, body=None, hdrs=None, host=None, auth=True):
    try:
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
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
        st = r.status; conn.close()
        return st, raw[:3000]
    except Exception as e:
        return 0, str(e).encode()[:300]

def show(tag, r):
    st, raw = r
    print('[%s] -> %d' % (tag, st))
    try:
        print('   ', json.dumps(json.loads(raw), indent=0)[:700])
    except Exception:
        print('   ', raw.decode(errors='replace')[:500])

# 1. 创建 bucket(默认 private)
st, raw = req('POST', '%s/projects/%s/branches/%s/buckets' % (API_BASE, P, B), {'name': BUCKET})
show('create bucket', (st, raw))
if st not in (200, 201):
    print('create failed, abort'); sys.exit()

# 2. presign upload
st, raw = req('POST', '%s/projects/%s/branches/%s/buckets/%s/objects/%s/presign' % (API_BASE, P, B, BUCKET, OBJ),
              {'operation': 'upload', 'content_type': 'text/plain'})
show('presign upload', (st, raw))
pr = json.loads(raw)
u = pr['url']; hdrs = pr.get('headers', {})
print('   url host:', urllib.parse.urlparse(u).netloc, '| path:', urllib.parse.urlparse(u).path[:120])
# PUT 内容:纯 SigV4 签名请求,不带 Authorization header
up = urllib.parse.urlparse(u)
st2, raw2 = req('PUT', up.path + '?' + up.query, 'K_BUCKET_PROBE_1', hdrs, host=up.netloc, auth=False)
show('PUT object', (st2, raw2))

# 3. list objects
st, raw = req('GET', '%s/projects/%s/branches/%s/buckets/%s/objects' % (API_BASE, P, B, BUCKET))
show('list objects', (st, raw))

# 4. session download
st, raw = req('GET', '%s/projects/%s/branches/%s/buckets/%s/objects/%s/download' % (API_BASE, P, B, BUCKET, OBJ))
show('session download', (st, raw))

# 5. presign download URL 直接 GET(无 console cookie——纯签名 URL 免认证?)
st, raw = req('POST', '%s/projects/%s/branches/%s/buckets/%s/objects/%s/presign' % (API_BASE, P, B, BUCKET, OBJ),
              {'operation': 'download'})
show('presign download', (st, raw))
try:
    pr2 = json.loads(raw)
    u2 = pr2['url']
    st3, raw3 = req('GET', urllib.parse.urlparse(u2).path + '?' + urllib.parse.urlparse(u2).query,
                    hdrs=None, host=urllib.parse.urlparse(u2).netloc, auth=False)
    show('GET presigned URL (no cookie)', (st3, raw3))
except Exception as e:
    print('presign dl parse err', e)

# 6. 创建子分支
st, raw = req('POST', '%s/projects/%s/branches' % (API_BASE, P), {'name': 'k-br-child', 'parent_id': B})
show('create child branch', (st, raw))
CB = None
try:
    CB = json.loads(raw)['branch']['id']
except Exception:
    try:
        CB = json.loads(raw)['id']
    except Exception:
        CB = None
print('child branch id:', CB)

if CB:
    time.sleep(2)
    # 7. 子分支 list buckets(继承?)
    st, raw = req('GET', '%s/projects/%s/branches/%s/buckets' % (API_BASE, P, CB))
    show('child list buckets(inherited?)', (st, raw))
    # 8. 子分支 download 继承对象
    st, raw = req('GET', '%s/projects/%s/branches/%s/buckets/%s/objects/%s/download' % (API_BASE, P, CB, BUCKET, OBJ))
    show('child download inherited obj', (st, raw))
    # 9. 子分支删除继承对象 → 父分支还在?(隔离语义)
    st, raw = req('DELETE', '%s/projects/%s/branches/%s/buckets/%s/objects/%s' % (API_BASE, P, CB, BUCKET, OBJ))
    show('child delete inherited obj', (st, raw))
    # 10. 父分支确认对象还在
    st, raw = req('GET', '%s/projects/%s/branches/%s/buckets/%s/objects/%s/download' % (API_BASE, P, B, BUCKET, OBJ))
    show('parent download after child delete', (st, raw))
    # 11. 子分支 list(墓碑语义)
    st, raw = req('GET', '%s/projects/%s/branches/%s/buckets/%s/objects' % (API_BASE, P, CB, BUCKET))
    show('child list after delete(tombstone?)', (st, raw))

# 12. 清理:删对象 + 删 bucket + 删子分支
req('DELETE', '%s/projects/%s/branches/%s/buckets/%s/objects/%s' % (API_BASE, P, B, BUCKET, OBJ), hdrs=HEADERS_TEST)
req('DELETE', '%s/projects/%s/branches/%s/buckets/%s' % (API_BASE, P, B, BUCKET), hdrs=HEADERS_TEST)
if CB:
    req('DELETE', '%s/projects/%s/branches/%s' % (API_BASE, P, CB), hdrs=HEADERS_TEST)
# 清理上次残留分支(如有)
for bid in ('br-twilight-firefly-w2nnbexb',):
    stc, _ = req('GET', '%s/projects/%s/branches/%s' % (API_BASE, P, bid))
    if stc == 200:
        req('DELETE', '%s/projects/%s/branches/%s' % (API_BASE, P, bid), hdrs=HEADERS_TEST)
        print('cleaned leftover branch', bid)
st, raw = req('GET', '%s/projects/%s/branches/%s/buckets' % (API_BASE, P, B))
show('final bucket list', (st, raw))
print('done')
