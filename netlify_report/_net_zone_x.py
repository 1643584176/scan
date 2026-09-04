# -*- coding: utf-8 -*-
"""dns_zones 跨账号矩阵 + 归属模型 + 二次创建冲突 + transfer 语义"""
import http.client, ssl, gzip, brotli, json, sys, time, random, string
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, USER_A, USER_B

ctx = ssl.create_default_context()
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ZONE_A = '6a97ecc68ea37900af43734c'  # zz-ysjxponr.com (A 创建)
rnd = ''.join(random.choices(string.ascii_lowercase, k=8))

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
    print('%-58s %s | %s' % (tag, st, b[:230].replace('\n', ' ')))
    return st, b

print('== 1. 跨账号可见性矩阵 ==')
probe('B GET /dns_zones (A zone 是否可见)', 'GET', '/api/v1/dns_zones', None, TOKEN_B)
probe('B GET A zone by id', 'GET', '/api/v1/dns_zones/%s' % ZONE_A, None, TOKEN_B)
probe('B GET A zone dns_records', 'GET', '/api/v1/dns_zones/%s/dns_records' % ZONE_A, None, TOKEN_B)
probe('A GET A zone by id', 'GET', '/api/v1/dns_zones/%s' % ZONE_A)
probe('B DELETE A zone', 'DELETE', '/api/v1/dns_zones/%s' % ZONE_A, None, TOKEN_B)
probe('B PUT transfer A zone -> B', 'PUT', '/api/v1/dns_zones/%s/transfer' % ZONE_A,
      {'account': '6a97b6454fef0db964f75db6'}, TOKEN_B)
print()
print('== 2. 二次创建冲突(同域两次) ==')
st, b = probe('A POST 同名 zone 二次', 'POST', '/api/v1/dns_zones', {'name': 'zz-ysjxponr.com'})
st, b = probe('A POST 新域名 zz2-%s.com' % rnd, 'POST', '/api/v1/dns_zones', {'name': 'zz2-%s.com' % rnd})
print()
print('== 3. 知名域名预注册限制 ==')
for nm in ['apple.com', 'netlify.com', 'google.com', 'zz3-%s.com' % rnd]:
    st, b = probe('POST zone name=%s' % nm, 'POST', '/api/v1/dns_zones', {'name': nm})
    if st == 201:
        import re
        m = re.search(r'"id":"([0-9a-f]{24})"', b)
        if m:
            probe('  cleanup delete %s' % nm, 'DELETE', '/api/v1/dns_zones/%s' % m.group(1))
print('done')
