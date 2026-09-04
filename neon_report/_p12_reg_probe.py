# -*- coding: utf-8 -*-
"""探测控制面注册流程可用性(email 密码注册,非 OAuth):
1. console 注册页/API 形态
2. keycloak register 端点状态
3. 判断能否注册第二控制面账号(IDOR 测试解锁)
"""
import http.client, ssl, urllib.parse

ctx = ssl.create_default_context()

def probe(host, path, method='GET', headers=None, body=None, port=443):
    try:
        conn = http.client.HTTPSConnection(host, port, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        if headers:
            h.update(headers)
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        raw = r.read()
        out = {
            'status': r.status,
            'hdrs': dict((k.lower(), v[:150]) for k, v in r.getheaders()),
            'body': raw.decode('utf-8', 'replace')[:600].replace('\n', ' '),
        }
        conn.close()
        return out
    except Exception as e:
        return {'status': -1, 'hdrs': {}, 'body': 'EXC %s' % e}

# 1. console 前端注册页面
r = probe('console-stage.neon.build', '/sign_up')
print('[sign_up page] %d loc=%s' % (r['status'], r['hdrs'].get('location', '')), flush=True)

# 2. keycloak 注册端点(直接)
r = probe('console-stage.neon.build', '/auth/keycloak/register')
print('[kc register] %d loc=%s body=%s' % (r['status'], r['hdrs'].get('location', ''), r['body'][:200]), flush=True)

# 3. 控制面注册 API(console 前端调用形态)
r = probe('console-stage.neon.build', '/api/register', 'POST',
          {'Content-Type': 'application/json'},
          b'{"email":"probe@example.com","password":"Xx12345678!"}')
print('[api/register] %d %s' % (r['status'], r['body'][:300]), flush=True)

# 4. keycloak auth 端点注册(表单流程, 模拟页面)
params = urllib.parse.urlencode({
    'client_id': 'neon-console',
    'redirect_uri': 'https://console-stage.neon.build/auth/keycloak/callback',
    'response_type': 'code', 'scope': 'openid profile email',
})
r = probe('console-stage.neon.build', '/auth/keycloak/register?' + params)
print('[kc register+params] %d loc=%s body=%s' % (r['status'], r['hdrs'].get('location', ''), r['body'][:250]), flush=True)
