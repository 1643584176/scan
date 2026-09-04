# -*- coding: utf-8 -*-
"""Netlify:agent-runner 归属校验矩阵(cookie 用户 vs accountId)"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B
ctx = ssl.create_default_context()

ACC_A_UUID = '6a979dd2ae93f47d55b62897'
ACC_B_UUID = '6a97b6454fef0db964f75db6'

def req(host, path, method='POST', raw=None, headers=None, cookie=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept': 'application/json', 'Cookie': cookie or COOKIE_A,
         'Origin': 'https://app.netlify.com'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=raw, headers=h)
    r = conn.getresponse(); raw2 = r.read()
    st = r.status; conn.close()
    return st, raw2[:300].decode('utf-8', 'replace')

fname = 'ar-x-%d.txt' % int(time.time())
content = b'test'

print('=== upload 归属 ===')
tests = [
    ('A-cookie + A-acc', COOKIE_A, ACC_A_UUID),
    ('A-cookie + B-acc', COOKIE_A, ACC_B_UUID),
    ('B-cookie + B-acc', COOKIE_B, ACC_B_UUID),
    ('B-cookie + A-acc', COOKIE_B, ACC_A_UUID),
]
for tag, ck, acc in tests:
    p = '/api/agent-runner-file-upload?accountId=%s&filename=%s' % (acc, fname)
    s, b = req('app.netlify.com', p, raw=content, headers={'Content-Type': 'text/plain'}, cookie=ck)
    print('%-18s -> %d %s' % (tag, s, b[:180]))

print()
print('=== delete 归属与错误形态(cookie=A)===')
for acc, tag in [(ACC_A_UUID, 'A-acc'), (ACC_B_UUID, 'B-acc')]:
    for fk in ['nonexistent-key-xyz', 'abc123', '00000000-0000-0000-0000-000000000000']:
        p = '/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (acc, fk)
        s, b = req('app.netlify.com', p)
        print('acc=%-6s fk=%-34s -> %d %s' % (tag, fk, s, b[:160]))
