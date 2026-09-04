# -*- coding: utf-8 -*-
"""用真实 SITE_A/account 重打全部 GET path, 暴露假 id 下被 404 掩盖的活资源端点"""
import http.client, ssl, gzip, brotli, json, sys, re, time
import yaml
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ACC_A = '6a979dd2ae93f47d55b62897'
USER_A = '6a979dd2ae93f47d55b62895'

def req(method, path, token=TOKEN_A, timeout=20):
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

def fill(path):
    p = ('/api/v1' + path) if not path.startswith('/api/v1') else path
    p = p.replace('{site_id}', SITE_A).replace('{account_id}', ACC_A) \
         .replace('{user_id}', USER_A).replace('{deploy_id}', '6a97c9e3083c963fd210b895')
    p = re.sub(r'\{[^}]+\}', 'zz-fake-0001', p)
    return p

with open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8') as f:
    spec = yaml.safe_load(f)

print('== 真实资源 GET 全量 ==')
seen = set()
for p, ops in spec['paths'].items():
    if 'get' not in ops:
        continue
    pp = fill(p)
    if pp in seen:
        continue
    seen.add(pp)
    st, b = req('GET', pp)
    # 只输出: 200 类 / 或响应非标准 404(说明有内容)
    if st == 200:
        body = b[:180].replace('\n', ' ')
        print('%-76s %s | %s' % (pp, st, body))
    elif st == 204:
        print('%-76s %s |' % (pp, st))
    time.sleep(0.04)
print('done')
