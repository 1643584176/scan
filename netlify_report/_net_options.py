# -*- coding: utf-8 -*-
"""1) purge 跨账号  2) OPTIONS 全 path 探 Allow: 找文档外影子方法"""
import http.client, ssl, gzip, brotli, json, sys, re
import yaml
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

ctx = ssl.create_default_context()
SLUG_A = '1643584176'
ACC_A = '6a979dd2ae93f47d55b62897'
DID = '6a97c9e3083c963fd210b895'

def req(method, path, body=None, token=None, timeout=15):
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
    allow = r.getheader('Allow', '')
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, allow, txt

print('== 1. purge 跨账号 ==')
for tag, tok, body in [
    ('A purge 自己 site', TOKEN_A, {'site_id': SITE_A}),
    ('B purge A site', TOKEN_B, {'site_id': SITE_A}),
    ('B purge A slug', TOKEN_B, {'site_slug': SLUG_A}),
    ('B purge 任意 domain', TOKEN_B, {'domain': 'example.com'}),
]:
    st, a, b = req('POST', '/api/v1/purge', body, tok)
    print('%-24s %s | %s' % (tag, st, b[:100]))

print()
print('== 2. OPTIONS 全 path ==')
with open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8') as f:
    spec = yaml.safe_load(f)
paths = spec['paths']

def sub(p):
    if not p.startswith('/api/v1'):
        p = '/api/v1' + p
    p = p.replace('{site_id}', SITE_A).replace('{account_id}', ACC_A)
    p = p.replace('{account_slug}', SLUG_A).replace('{deploy_id}', DID)
    p = re.sub(r'\{[^}]+\}', 'zz-fake-0001', p)
    return p

doc_methods = {'get', 'post', 'put', 'patch', 'delete'}
rows = []
for p in sorted(paths.keys()):
    doc = set(k for k in paths[p].keys() if k in doc_methods)
    pp = sub(p)
    st, allow, b = req('OPTIONS', pp, token=TOKEN_A)
    impl = set(m.strip().upper() for m in allow.split(',')) if allow else set()
    impl_l = {m.lower() for m in impl}
    extra = impl_l - doc          # 生产有, 文档没写 = 影子方法
    missing = doc - impl_l        # 文档有, 生产 Allow 没写
    if extra or (st != 404 and not allow and doc):
        rows.append((p, st, allow[:60], sorted(doc), sorted(extra)))

print('%-78s %-5s %-16s %s' % ('path', 'st', 'allow', '影子方法'))
for p, st, allow, doc, extra in rows:
    if extra:
        print('%-78s %-5s %-16s SHADOW: %s (doc: %s)' % (p, st, allow, extra, doc))
    else:
        print('%-78s %-5s %-16s doc: %s' % (p, st, allow or '-', doc))
print('done')
