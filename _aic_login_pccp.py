# -*- coding: utf-8 -*-
"""AIC 第十六轮:用真实用户名 pccp 登录 + 会话验证
预期结果表:
  成立 -> pccp+密码登录成功,拿 tokenId
  不成立 -> 密码错误(确认账号状态)
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER = 'pccp'
PASS = 'Agent360User$5h2!QxR'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
H = {'User-Agent': 'research-1643',
     'Accept-API-Version': 'resource=1.0, protocol=1.0',
     'Content-Type': 'application/json'}
S.headers.update(H)

r = S.post(AUTH, json={}, timeout=15, verify=False)
d = r.json()
authId = d.get('authId')
print('init:', r.status_code, [c['type'] for c in d.get('callbacks', [])])

callbacks = []
for cb in d.get('callbacks', []):
    t = cb['type']
    inp = []
    if t == 'NameCallback':
        inp = [{'name': 'IDToken1', 'value': USER}]
    elif t == 'PasswordCallback':
        inp = [{'name': 'IDToken2', 'value': PASS}]
    else:
        inp = [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
    callbacks.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})

r2 = S.post(AUTH, json={'authId': authId, 'callbacks': callbacks}, timeout=15, verify=False)
d2 = r2.json()
tok = d2.get('tokenId')
print('login:', r2.status_code, 'token:', tok[:60] if tok else None)
if not tok:
    print('resp:', json.dumps({k: v for k, v in d2.items() if k != 'authId'})[:400])
else:
    with open(r'D:\scan\_aic_sess.txt', 'w') as f:
        f.write(tok)
    # 用会话验证
    S2 = requests.Session()
    S2.trust_env = False
    S2.proxies = {'http': None, 'https': None}
    S2.headers.update({'User-Agent': 'research-1643', 'Cookie': 'iPlanetDirectoryPro=' + tok,
                       'Accept-API-Version': 'resource=2.1, protocol=1.0'})
    for p in ['/am/json/realms/root/realms/alpha/sessions?_action=getSessionInfo',
              '/am/json/realms/root/realms/alpha/users?_queryFilter=true',
              '/am/json/realms/root/realms/alpha/users/self',
              '/am/json/realms/root/realms/alpha/groups?_queryFilter=true',
              '/am/json/realms/root/realms/alpha/applications?_queryFilter=true',
              '/iga/governance/user/db3d6356-61a0-4684-9eaa-c1353dfa44d9/grants?pageSize=5']:
        kw = {}
        if '_action=getSessionInfo' in p:
            kw['json'] = {'withCredentials': True}
        r3 = S2.request('POST' if '_action=' in p else 'GET', BASE + p, timeout=12, verify=False, **kw)
        print('%-85s -> %d %s' % (p, r3.status_code, r3.text[:150].replace('\n', ' ')))
