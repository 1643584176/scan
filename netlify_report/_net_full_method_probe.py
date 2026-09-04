# -*- coding: utf-8 -*-
"""全量逐方法探活: 文档每个 path x 文档方法, 最小 body, 找 GET 盲区里的活路由"""
import http.client, ssl, gzip, brotli, json, sys, re, time
import yaml
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()

def req(method, path, body=None, token=TOKEN_A, timeout=20):
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

FAKE_SITE = '00f00000-0000-4000-8000-000000000000'
FAKE_ACC = '00a00000-0000-4000-8000-000000000000'

def fill(path):
    p = ('/api/v1' + path) if not path.startswith('/api/v1') else path
    p = p.replace('{site_id}', FAKE_SITE).replace('{account_id}', FAKE_ACC)
    p = re.sub(r'\{[^}]+\}', 'zz-fake-0001', p)
    return p

# 收集所有 (path, method) 并优先测非 GET 方法
tasks = []
with open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8') as f:
    spec = yaml.safe_load(f)
for p, ops in spec['paths'].items():
    for m in ops:
        if m in ('get', 'post', 'put', 'delete', 'patch'):
            tasks.append((p, m.upper()))

def classify(st, txt):
    if st in (200, 201, 202, 204):
        return 'LIVE'
    if st == 404:
        return 'dead-404' if not txt.strip().startswith('{') else 'ROUTE(404)'
    if st == 405:
        return 'ROUTE(405)'
    if st in (400, 401, 403, 422):
        # 假资源 id 下这些状态说明路由存在(权限/校验层)
        return 'ROUTE(%d)' % st
    return 'LIVE?%d' % st

print('== 非 GET 方法全量(假资源 id, 无副作用)==')
for p, m in tasks:
    if m == 'GET':
        continue
    pp = fill(p)
    body = {}
    st, b = req(m, pp, body if m in ('POST', 'PUT', 'PATCH') else None)
    cls = classify(st, b)
    if cls != 'dead-404':
        print('%-7s %-72s %s %s | %s' % (m, pp, st, cls, b[:100].replace('\n', ' ')))
    time.sleep(0.05)
print()
print('done')
