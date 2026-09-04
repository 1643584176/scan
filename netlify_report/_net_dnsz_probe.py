# -*- coding: utf-8 -*-
"""清理误建站点/deploy key + dns_zones 精确探测(创建/transfer/记录)"""
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
    print('%-52s %s | %s' % (tag, st, b[:260].replace('\n', ' ')))
    return st, b

print('== 0. 清理副作用 ==')
st, b = probe('DELETE 误建站点 2bff6530', 'DELETE', '/api/v1/sites/2bff6530-c9e8-41e3-9f42-2e857b88dd7e')
st, b = probe('DELETE deploy key 6a97ec5e', 'DELETE', '/api/v1/deploy_keys/6a97ec5edbddc500e5173073')

print()
print('== 1. dns_zones 形态 ==')
# 各种 name 形态看校验
rnd = ''.join(random.choices(string.ascii_lowercase, k=8))
for name in [None, '', 'zz-%s.com' % rnd, 'zz-%s.netlify.app' % rnd, 'localhost', '127.0.0.1']:
    body = {} if name is None else {'name': name}
    st, b = probe('POST dns_zones name=%r' % (name or ''), 'POST', '/api/v1/dns_zones', body)
print()
print('== 2. GET 我的 zones 列表 ==')
st, b = probe('GET /dns_zones', 'GET', '/api/v1/dns_zones')
st, b = probe('GET /dns_zones?account_slug=...', 'GET', '/api/v1/dns_zones?account_slug=1643584176')
print()
print('== 3. agent_runners/upload_url 带 account_id ==')
ACC = '6a979dd2ae93f47d55b62897'
st, b = probe('POST upload_url account_id=A', 'POST', '/api/v1/agent_runners/upload_url', {'account_id': ACC})
print()
print('== 4. POST /accounts 枚举 account type ==')
for t in ['personal', 'organization', 'team', 'org', 'enterprise', 'business']:
    st, b = probe('POST accounts type=%s' % t, 'POST', '/api/v1/accounts', {'type': t, 'name': 'zz-t-%s' % t})
print('done')
