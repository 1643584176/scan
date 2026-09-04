# -*- coding: utf-8 -*-
"""env API 收尾变异: PUT 更新形态 / values 重复与类型 / key 边界 / context 过滤语义
全部在 B 站操作, 测完清理
"""
import http.client, ssl, gzip, brotli, json, sys, random
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
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

def get_env():
    st, b = req('GET', '/api/v1/sites/%s/env' % SITE_B, token=TOKEN_B)
    return st, b

def add_env(key, vals, tag):
    body = [{'key': key, 'values': vals}]
    st, b = req('POST', '/api/v1/accounts/%s/env?site_id=%s' % (ACC_B, SITE_B), body, TOKEN_B)
    print('%-40s %s | %s' % (tag, st, b[:120]))
    return st, b

def del_env(key):
    st, b = req('DELETE', '/api/v1/accounts/%s/env/%s?site_id=%s' % (ACC_B, key, SITE_B), token=TOKEN_B)
    return st

R = random.randint(1000, 9999)
print('== 1. 基线写入 + PUT 更新形态 ==')
K1 = 'T_P%s' % R
add_env(K1, [{'context': 'production', 'value': 'v1'}], 'POST 基线 K1')
# PUT 更新尝试(先拿 value id)
st, b = get_env()
vid = None
try:
    j = json.loads(b)
    for e in j:
        if e.get('key') == K1:
            vid = e['values'][0]['id']
except Exception:
    pass
print('value id =', vid)
puts = [
    ('PUT acc env/key', '/api/v1/accounts/%s/env/%s?site_id=%s' % (ACC_B, K1, SITE_B)),
    ('PUT acc env',     '/api/v1/accounts/%s/env?site_id=%s' % (ACC_B, SITE_B)),
    ('PATCH acc env/key','/api/v1/accounts/%s/env/%s?site_id=%s' % (ACC_B, K1, SITE_B)),
]
for tag, p in puts:
    st, b = req('PUT' if 'PUT' in tag else 'PATCH', p,
                [{'key': K1, 'values': [{'id': vid, 'context': 'production', 'value': 'v2'}]}], TOKEN_B)
    print('%-24s %s | %s' % (tag, st, b[:150]))

print()
print('== 2. values/类型/key 边界变异 ==')
variants = [
    ('双 production 同 key', K1 + 'D', [{'context': 'production', 'value': 'a'}, {'context': 'production', 'value': 'b'}]),
    ('value 是数字',         K1 + 'N', [{'context': 'production', 'value': 12345}]),
    ('value 是对象',         K1 + 'O', [{'context': 'production', 'value': {'a': 1}}]),
    ('value 是数组',         K1 + 'A', [{'context': 'production', 'value': ['x']}]),
    ('value 是 null',       K1 + 'L', [{'context': 'production', 'value': None}]),
    ('value 含换行/控制符',   K1 + 'C', [{'context': 'production', 'value': 'a\nb\x00c\r'}]),
    ('key 超长 300',        'K' * 300, [{'context': 'production', 'value': 'v'}]),
    ('value 超长 100k',     K1 + 'B', [{'context': 'production', 'value': 'x' * 100000}]),
    ('context=deploy-preview', K1 + 'V', [{'context': 'deploy-preview', 'value': 'v'}]),
    ('context=branch+param 非保留', K1 + 'F', [{'context': 'branch', 'value': 'v', 'context_parameter': 'dev-%s' % R}]),
]
for tag, key, vals in variants:
    add_env(key, vals, tag)

print()
print('== 3. 当前 env 全量(GET 明文)==')
st, b = get_env()
print(st, b[:1500])

print()
print('== 4. context 过滤语义: 读 production vs branch ==')
for q in ['', '?context=production', '?context=branch&context_parameter=dev-%s' % R]:
    st, b = req('GET', '/api/v1/sites/%s/env%s' % (SITE_B, q), token=TOKEN_B)
    print('GET %-40s %s | %s' % (q or '(无参)', st, b[:300]))

print()
print('== 5. 清理全部 ==')
st, b = get_env()
try:
    keys = [e.get('key') for e in json.loads(b)]
except Exception:
    keys = []
for k in keys:
    print('del', k, del_env(k))
st, b = get_env()
print('final:', st, b[:100])
print('done')
