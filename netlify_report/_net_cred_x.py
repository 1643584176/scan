# -*- coding: utf-8 -*-
"""高敏凭证端点跨账号矩阵: ai-gateway token / database 连接串 / audit / members / sites
A 资源 + B token = 越权读? A token 基线对照
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

ctx = ssl.create_default_context()
SLUG_A = '1643584176'
ACC_A = '6a979dd2ae93f47d55b62897'
ACC_B = '6a97b6454fef0db964f75db6'

def req(method, path, token=None, timeout=20):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

paths = [
    ('ai-gateway token', '/api/v1/sites/%s/ai-gateway/token' % SITE_A),
    ('database 连接串',   '/api/v1/sites/%s/database' % SITE_A),
    ('database branches', '/api/v1/sites/%s/database/branches' % SITE_A),
    ('database snapshots', '/api/v1/sites/%s/database/snapshots' % SITE_A),
    ('account audit',     '/api/v1/accounts/%s/audit' % ACC_A),
    ('slug members',      '/api/v1/%s/members' % SLUG_A),
    ('slug sites',        '/api/v1/%s/sites' % SLUG_A),
    ('account env',       '/api/v1/accounts/%s/env' % ACC_A),
    ('deploy keys',       '/api/v1/deploy_keys'),
    ('account 详情',       '/api/v1/accounts/%s' % ACC_A),
]
print('%-22s %-12s %-12s %s' % ('path', 'A自己', 'B跨账号', '备注'))
for tag, p in paths:
    stA, bA = req('GET', p, TOKEN_A)
    stB, bB = req('GET', p, TOKEN_B)
    # 判定
    mark = ''
    if stA == 200 and stB == 200:
        # 响应是否一样?若 B 能读到 A 的数据 = 越权
        same = 'SAME-CONTENT' if bA == bB else 'diff'
        mark = '<<< B 也 200! %s' % same
    elif stA == 200 and stB in (401, 403, 404):
        mark = 'ok(拦截)'
    elif stA != 200:
        mark = 'A 基线即 %s' % stA
    print('%-22s %-12s %-12s %s' % (tag, '%s|%s' % (stA, bA[:40]), '%s|%s' % (stB, bB[:60]), mark))

print()
print('== B 跨账号读到的内容细节(B token 响应)==')
for tag, p in paths:
    stB, bB = req('GET', p, TOKEN_B)
    if stB == 200:
        print('--- %s:\n%s' % (tag, bB[:500]))
print('done')
