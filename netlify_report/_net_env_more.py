# -*- coding: utf-8 -*-
"""env: 1) GET 明文确认  2) 删除接口 + 清理 T_E5030  3) account 级 env(无 site_id)交叉
4) context/values 变异(免费 plan 限制内)
"""
import http.client, ssl, gzip, brotli, json, sys, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ACC_A = '6a979dd2ae93f47d55b62897'
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

print('== 1. GET B env 明文确认 ==')
st, b = req('GET', '/api/v1/sites/' + SITE_B + '/env', TOKEN_B)
print(st, b[:400])
print()

print('== 2. 删除接口形态 + 清理 ==')
delpaths = [
    ('DELETE', '/api/v1/accounts/' + ACC_B + '/env?site_id=' + SITE_B + '&key=T_E5030'),
    ('DELETE', '/api/v1/sites/' + SITE_B + '/env/T_E5030'),
    ('DELETE', '/api/v1/sites/' + SITE_B + '/env?key=T_E5030'),
    ('DELETE', '/api/v1/accounts/' + ACC_B + '/env/T_E5030?site_id=' + SITE_B),
]
for m, p in delpaths:
    st, b = req(m, p, token=TOKEN_B)
    print('%-7s %-75s -> %s | %s' % (m, p, st, b[:100]))
    if st in (200, 204):
        break
st, b = req('GET', '/api/v1/sites/' + SITE_B + '/env', TOKEN_B)
print('after del:', st, b[:200])
print()

print('== 3. account 级 env(无 site_id)交叉 ==')
for tag, tok, acc in [
    ('A tok accA (自己)', TOKEN_A, ACC_A),
    ('A tok accB (跨账号!)', TOKEN_A, ACC_B),
    ('B tok accA (跨账号!)', TOKEN_B, ACC_A),
    ('B tok accB (自己)', TOKEN_B, ACC_B),
]:
    st, b = req('GET', '/api/v1/accounts/%s/env' % acc, token=tok)
    print('GET  %-25s -> %s | %s' % (tag, st, b[:150]))

# POST account env 交叉(创建到对端 account)
K3 = 'T_A%s' % random.randint(1000, 9999)
body = [{'key': K3, 'values': [{'context': 'production', 'value': 'acctest'}]}]
for tag, tok, acc in [
    ('A tok -> accB (跨账号写!)', TOKEN_A, ACC_B),
    ('B tok -> accB (自己)', TOKEN_B, ACC_B),
]:
    st, b = req('POST', '/api/v1/accounts/%s/env' % acc, body, tok)
    print('POST %-25s -> %s | %s' % (tag, st, b[:150]))
    if st in (200, 201):
        for t2, t3 in [(TOKEN_A, 'A'), (TOKEN_B, 'B')]:
            s2, b2 = req('GET', '/api/v1/accounts/%s/env' % acc, token=t2)
            print('   verify via %s: %s | %s' % (t3, s2, b2[:150]))
print()

print('== 4. context/values 变异(免费限制内, B 站临时 key) ==')
K4 = 'T_C%s' % random.randint(1000, 9999)
variants = [
    ('多 values(prod+branch)', [{'key': K4, 'values': [
        {'context': 'production', 'value': 'v-p'},
        {'context': 'branch', 'value': 'v-b', 'context_parameter': 'main'}]}]),
    ('context=all', [{'key': K4, 'values': [{'context': 'all', 'value': 'v-all'}]}]),
    ('context=*', [{'key': K4, 'values': [{'context': '*', 'value': 'v-s'}]}]),
    ('context 空串', [{'key': K4, 'values': [{'context': '', 'value': 'v-e'}]}]),
    ('无 context', [{'key': K4, 'values': [{'value': 'v-n'}]}]),
    ('key 带点号', [{'key': 'T.dot' + K4, 'values': [{'context': 'production', 'value': 'v'}]}]),
    ('key 带等号', [{'key': 'T=eq' + K4, 'values': [{'context': 'production', 'value': 'v'}]}]),
]
for tag, bd in variants:
    st, b = req('POST', '/api/v1/accounts/' + ACC_B + '/env?site_id=' + SITE_B, bd, TOKEN_B)
    print('%-32s -> %s | %s' % (tag, st, b[:160]))
print('done')
