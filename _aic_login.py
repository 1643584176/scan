# -*- coding: utf-8 -*-
"""AIC 登录:ForgeRock AM callbacks 认证流程
流程:空 POST -> authId+callbacks -> 填用户名密码 -> tokenId
注意:凭据仅本地使用,脚本不进 git
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER = '1643584176@qq.com'
PASS = 'Agent360User$5h2!QxR'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Accept-API-Version': 'resource=1.0, protocol=1.0',
                  'Content-Type': 'application/json'})

# 1. 拿 authId + callbacks
r = S.post(AUTH, json={}, timeout=15, verify=False)
print('step1:', r.status_code)
d = r.json()
authId = d.get('authId')
print('authId:', authId[:80] if authId else None)
print('callbacks:')
for cb in d.get('callbacks', []):
    print('  type=%s outputs=%s' % (cb['type'], [o.get('value') for o in cb.get('output', [])]))

# 循环处理多轮 callbacks,直到拿到 tokenId
for round_i in range(1, 7):
    print('\n=== round %d ===' % round_i)
    callbacks = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        out = [o.get('value') for o in cb.get('output', [])]
        print('  callback type=%s outputs=%s' % (t, out))
        inp = []
        if t == 'NameCallback':
            inp = [{'name': 'IDToken1', 'value': USER}]
        elif t == 'PasswordCallback':
            inp = [{'name': 'IDToken2', 'value': PASS}]
        elif t == 'ChoiceCallback':
            inp = [{'name': 'IDToken3', 'value': 0}]
        elif t == 'TextOutputCallback':
            inp = []
        else:
            inp = [{'name': k.get('name'), 'value': ''} for k in cb.get('input', [])]
        callbacks.append({'type': t, 'output': cb.get('output', []), 'input': inp})

    r2 = S.post(AUTH, json={'authId': authId, 'callbacks': callbacks}, timeout=15, verify=False)
    d = r2.json()
    tokenId = d.get('tokenId')
    if tokenId:
        print('\nTOKEN_ID:', tokenId[:100])
        with open(r'D:\scan\_aic_token.txt', 'w') as f:
            f.write(tokenId)
        print('saved to _aic_token.txt')
        break
    authId = d.get('authId')
    if not authId:
        print('no authId, final:', r2.text[:500])
        break
    if round_i == 6:
        print('\nmax rounds reached, last response:', r2.text[:500])
