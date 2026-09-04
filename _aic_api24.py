# -*- coding: utf-8 -*-
"""AIC 第四十四轮:.well-known 完整 dump 找隐藏端点 + tokeninfo/profile/IGA 补测
上轮信号:.well-known 泄露 par 端点(根 realm 路径 /am/oauth2/alpha/par)。
本轮:
A. 完整 dump openid-configuration 所有端点 URL(找未测端点:par/device/introspection/
   registration/end_session)
B. tokeninfo GET 方式重试
C. profile scope authorize 失败原因(响应体)
D. IGA requests 创建 action 枚举(上轮未跑到)
E. PAR 端点探测(存在性 + 行为)
预期结果表:
  有信号 -> 未测端点存在且行为异常;PAR 接受/返回非标准错误;profile 可拿 token
"""
import requests, urllib3, json, time
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

def get_token(scope):
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
        '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote(scope, safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    if 'code=' in loc:
        code = loc.split('code=')[1].split('&')[0]
        r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                                    'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
        return r2.json().get('access_token')
    print('  authorize 无 code: %d %s %s' % (r.status_code, loc[:120], r.text[:200].replace('\n', ' ')))
    return None

print('\n=== A. openid-configuration 完整端点 ===')
r = S.get(BASE + '/am/oauth2/realms/alpha/.well-known/openid-configuration', timeout=15, verify=False)
j = r.json()
for k, v in sorted(j.items()):
    if isinstance(v, str) and v.startswith('http'):
        print('%-42s %s' % (k, v))
    elif k in ('scopes_supported', 'grant_types_supported', 'response_types_supported',
               'token_endpoint_auth_methods_supported', 'claims_supported'):
        print('%-42s %s' % (k, v))

print('\n=== B. tokeninfo GET ===')
at = get_token('openid')
for m, body in [('GET', None), ('POST', {'token': at})]:
    try:
        if m == 'GET':
            r = S.get(BASE + '/am/oauth2/realms/alpha/tokeninfo?token=' + at, timeout=12, verify=False)
        else:
            r = S.post(BASE + '/am/oauth2/realms/alpha/tokeninfo', data=body, headers=FORM, timeout=12, verify=False)
        print('tokeninfo %s -> %d %s' % (m, r.status_code, r.text[:250].replace('\n', ' ')))
    except Exception as e:
        print('tokeninfo %s -> ERR %s' % (m, str(e)[:60]))
    time.sleep(0.5)

print('\n=== C. profile scope 失败原因 ===')
for sc in ['openid profile', 'profile email', 'openid email', 'openid profile email']:
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
        '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote(sc, safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    print('scope=%-22s -> %d code=%s %s' % (sc, r.status_code, 'Y' if 'code=' in loc else 'N',
          (loc[:100] if 'code=' not in loc else loc.split('code=')[1][:20])))
    time.sleep(0.5)

print('\n=== D. IGA requests 创建 action 枚举 ===')
RP = '/iga/governance/user/%s/requests' % MY_ID
at_iga = get_token('openid fr:iga:*')
if at_iga:
    for act in ['createRequest', 'submit', 'start', 'initiate', 'apply', 'createAccessRequest',
                'requestAccess', 'submitRequest']:
        try:
            r = S.post(BASE + RP + '?_action=' + act,
                       json={'roles': [{'name': 'test'}]},
                       headers={'Authorization': 'Bearer ' + at_iga,
                                'Accept-API-Version': 'resource=2.1, protocol=1.0'},
                       timeout=12, verify=False)
            print('requests _action=%-18s -> %d %s' % (act, r.status_code, r.text[:120].replace('\n', ' ')))
        except Exception as e:
            print('requests _action=%-18s -> ERR %s' % (act, str(e)[:60]))
        time.sleep(0.5)

print('\n=== E. PAR 端点探测 ===')
for p in ['/am/oauth2/alpha/par', '/am/oauth2/realms/alpha/par']:
    try:
        r = S.post(BASE + p,
                   data={'client_id': 'endUserUIClient', 'response_type': 'code',
                         'redirect_uri': RU, 'scope': 'openid'},
                   headers=FORM, timeout=12, verify=False)
        print('PAR %-40s -> %d %s' % (p, r.status_code, r.text[:200].replace('\n', ' ')))
    except Exception as e:
        print('PAR %-40s -> ERR %s' % (p, str(e)[:60]))
    time.sleep(0.5)
