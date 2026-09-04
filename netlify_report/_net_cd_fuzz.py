# -*- coding: utf-8 -*-
"""custom_domain 字段攻击:格式接受矩阵 + 双站点绑定冲突测试
安全: 全部用编造域, 只操作 A/B 自有站点, 测完清理
"""
import http.client, ssl, gzip, brotli, json, sys, time, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if body is not None else None
    t0 = time.time()
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    dt = time.time() - t0
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, dt, txt

def get_dom(site, token):
    st, dt, b = req('GET', '/api/v1/sites/' + site, token=token)
    try:
        j = json.loads(b)
        return st, j.get('custom_domain'), j.get('domains'), str(j.get('ssl'))[:80], j.get('ssl_plan')
    except Exception:
        return st, '?', '?', b[:100], None

def patch_cd(site, token, val, label):
    st, dt, b = req('PATCH', '/api/v1/sites/' + site, {'custom_domain': val}, token=token)
    try:
        j = json.loads(b)
        echo = 'cd=%r' % j.get('custom_domain')
    except Exception:
        echo = b[:120]
    print('%-34s %s %5.1fs | %s | %s' % (label, st, dt, echo, b[:60]))
    return st

print('== 0. 双方初始状态 ==')
print('A:', get_dom(SITE_A, TOKEN_A))
print('B:', get_dom(SITE_B, TOKEN_B))

print()
print('== 1. 格式接受矩阵(A 站)==')
R = str(random.randint(1000, 9999))
formats = [
    ('plain',        'fuzz-%s.example.com' % R),
    ('with http',    'http://fuzz-http-%s.com' % R),
    ('with https',   'https://fuzz-https-%s.com' % R),
    ('with path',    'fuzz-path-%s.com/evil' % R),
    ('with port',    'fuzz-port-%s.com:8443' % R),
    ('wildcard',     '*.fuzz-wc-%s.com' % R),
    ('netlify.app',  'fuzz-na-%s.netlify.app' % R),
    ('comma two',    'fuzz-c1-%s.com, fuzz-c2-%s.com' % (R, R)),
    ('array',        None),  # 特殊处理
    ('object',       None),
    ('int',          None),
    ('bool',         None),
    ('empty str',    ''),
    ('unicode',      'fuzz-ü-%s.com' % R),
    ('uppercase',    'FUZZ-UP-%s.com' % R),
    ('trailing dot', 'fuzz-td-%s.com.' % R),
    ('long 300',     'fuzz-%s.com' % ('x' * 280)),
]
for label, val in formats:
    if label == 'array':
        st = patch_cd(SITE_A, TOKEN_A, ['fuzz-arr-%s.com' % R], 'arr:%s' % label)
    elif label == 'object':
        st = patch_cd(SITE_A, TOKEN_A, {'host': 'fuzz-obj-%s.com' % R}, 'obj:%s' % label)
    elif label == 'int':
        st = patch_cd(SITE_A, TOKEN_A, 12345, 'int:%s' % label)
    elif label == 'bool':
        st = patch_cd(SITE_A, TOKEN_A, True, 'bool:%s' % label)
    else:
        st = patch_cd(SITE_A, TOKEN_A, val, 'val:%s' % label)

print()
print('A after formats:', get_dom(SITE_A, TOKEN_A))

print()
print('== 2. 双站点绑定冲突测试 ==')
X = 'conflict-%s.example.com' % R
print('domain X =', X)
patch_cd(SITE_B, TOKEN_B, X, 'B 绑 X(先)')
print('B now:', get_dom(SITE_B, TOKEN_B))
patch_cd(SITE_A, TOKEN_A, X, 'A 绑 X(抢)')
print('A now:', get_dom(SITE_A, TOKEN_A))
print('B after A抢:', get_dom(SITE_B, TOKEN_B))
patch_cd(SITE_B, TOKEN_B, X, 'B 重绑 X(再抢回)')
print('A after B重绑:', get_dom(SITE_A, TOKEN_A))

print()
print('== 3. 清理 ==')
patch_cd(SITE_A, TOKEN_A, None, 'A 清空')
patch_cd(SITE_B, TOKEN_B, None, 'B 清空')
print('A final:', get_dom(SITE_A, TOKEN_A))
print('B final:', get_dom(SITE_B, TOKEN_B))
print('done')
