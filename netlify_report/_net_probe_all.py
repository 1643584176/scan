# -*- coding: utf-8 -*-
"""全量端点探活: GET 优先, 响应体区分死路由(文本404)/活路由(JSON404或200等)
占位符替换用 A 的资源
"""
import http.client, ssl, gzip, brotli, json, sys, re
import yaml
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()
SLUG_A = '1643584176'
ACC_A = '6a979dd2ae93f47d55b62897'
DID = '6a97c9e3083c963fd210b895'

with open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8') as f:
    spec = yaml.safe_load(f)

paths = spec['paths']

def sub(p):
    if not p.startswith('/api/v1'):
        p = '/api/v1' + p
    p = p.replace('{site_id}', SITE_A).replace('{account_id}', ACC_A)
    p = p.replace('{account_slug}', SLUG_A).replace('{deploy_id}', DID)
    # 剩余占位符 -> 随机假值
    p = re.sub(r'\{[^}]+\}', 'zz-fake-0001', p)
    return p

def req(method, path, token=TOKEN_A, timeout=15):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Authorization': 'Bearer ' + token}
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

def classify(st, txt):
    if st == 404 and not txt.strip().startswith('{'):
        return 'DEAD'   # 文本 Not Found = 路由不存在
    if st == 404:
        return '404-JSON'  # 活路由, 资源/权限拒绝
    return '%d-LIVE' % st

alive = []
dead = []
other = []
for p in sorted(paths.keys()):
    item = paths[p]
    if 'get' not in item:
        continue
    pp = sub(p)
    st, txt = req('GET', pp)
    c = classify(st, txt)
    if c == 'DEAD':
        dead.append(p)
    else:
        other.append((p, c, txt[:80]))
        if st != 404:
            alive.append((p, st, txt[:100]))

print('== 活路由(GET 非404)==')
for p, st, t in alive:
    print('%-85s %s | %s' % (p, st, t.replace('\n', ' ')))
print()
print('== 404-JSON(路由活但资源404)==')
for p, c, t in other:
    if '404-JSON' in c:
        print('%-85s %s' % (p, t))
print()
print('dead(纯文本404):', len(dead))
for p in dead:
    print('   ', p)
