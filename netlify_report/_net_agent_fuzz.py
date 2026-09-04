# -*- coding: utf-8 -*-
"""agent-runner 文件接口:上传拿 file_key,观察格式与校验"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ACC_A = '6a979dd2ae93f47d55b62897'
ACC_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, method='POST', body=None, headers=None, timeout=20):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if headers: h.update(headers)
    if body is not None and 'Content-Type' not in h:
        h['Content-Type'] = 'application/octet-stream'
    t0 = time.time()
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    hd = dict((k.lower(), v) for k, v in r.getheaders())
    b = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:300]
    conn.close()
    return st, dt, hd, b

def show(label, path, ck=COOKIE_A, method='POST', body=None, hdrs=None):
    st, dt, hd, b = req(path, ck, method=method, body=body, headers=hdrs)
    print('%-42s %s %5.1fs ct=%s | %s' % (label, st, dt, hd.get('content-type', '?'), b))
    return st, b

print('==== 1. 上传基线(ACC_A)====')
st, b = show('upload probe-a.txt', '/api/agent-runner-file-upload?accountId=%s&filename=probe-a.txt' % ACC_A,
             body=b'hello agent runner A')
key_a = None
try:
    key_a = json.loads(b)['file_key']
except Exception:
    print('!! parse fail, raw:', b)
print('KEY_A =', key_a)

print()
print('==== 2. 上传变体:filename 特殊字符 ====')
for lbl, fn in [('dotdot', '../probe-b.txt'), ('slash', 'dir/probe-c.txt'), ('url-ish', 'a%2Fb.txt'),
                ('empty', ''), ('unicode', '测试.txt')]:
    p = '/api/agent-runner-file-upload?accountId=%s&filename=%s' % (ACC_A, urllib.parse.quote(fn, safe=''))
    st, b = show('upload fn:%s' % lbl, p, body=b'x')
    if lbl == 'dotdot':
        try:
            print('   key:', json.loads(b).get('file_key'))
        except Exception:
            pass

print()
print('==== 3. 匿名上传 ====')
show('upload anon', '/api/agent-runner-file-upload?accountId=%s&filename=anon.txt' % ACC_A, None, body=b'x')

print()
print('==== 4. 上传到他人 accountId ====')
show('upload ACC_B w/ A cookie', '/api/agent-runner-file-upload?accountId=%s&filename=cross.txt' % ACC_B,
     body=b'cross account file')
print('done')
