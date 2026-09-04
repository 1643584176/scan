# -*- coding: utf-8 -*-
"""Better Auth 插件端点面探测(对应 2026-06 advisory 适用性):
api-key(CVE-2025-61928) / device-flow(GHSA-cq3f) / organization(GHSA-fmh4) / sso(GHSA-5rr4)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'
PREFIX = '/neondb/auth'

def req(method, path, body=None, cookie=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if cookie:
            h['Cookie'] = cookie
        conn.request(method, PREFIX + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

# 匿名探测(未认证):200=开放,401/403=存在但需认证,404=不存在
paths = [
    # api-key 插件(CVE-2025-61928)
    ('POST', '/api-key'), ('POST', '/api-key/create'), ('GET', '/api-key/list'),
    ('POST', '/api-key/verify'), ('GET', '/api-key/verify'), ('POST', '/api-key/delete'),
    ('GET', '/api-keys'), ('POST', '/api-keys'),
    # device flow
    ('POST', '/device-flow'), ('POST', '/device-flow/authorize'), ('POST', '/device-flow/verify'),
    ('POST', '/device-flow/grant'), ('GET', '/device-flow/authorize'),
    # organization 插件面
    ('GET', '/organization/list'), ('POST', '/organization/create'),
    ('GET', '/organization'), ('POST', '/organization/invite'),
    # sso 插件
    ('POST', '/sso/register'), ('GET', '/sso/available'),
    # admin 插件
    ('GET', '/admin/list-users'), ('POST', '/admin/create-user'),
    # 通用
    ('GET', '/api-key/test'), ('POST', '/api-key/test'),
    ('GET', '/session'), ('GET', '/user'), ('POST', '/sign-out'),
]
seen = set()
for method, p in paths:
    if (method, p) in seen:
        continue
    seen.add((method, p))
    st, raw = req(method, p)
    snippet = raw[:110].replace('\n', ' ')
    if st == 404:
        continue  # 不存在(静默)
    print('[%s %s] -> %d %s' % (method, p, st, snippet), flush=True)
    time.sleep(0.2)
print('(404 静默省略;以上为所有非 404 端点)')
