# -*- coding: utf-8 -*-
"""AIC 登录调试:打印完整响应 + 尝试多种认证树/用户名格式"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER_VARIANTS = ['1643584176@qq.com', '1643584176']
PASS = 'Agent360User$5h2!QxR'
TREES = [None, 'Login', 'login', 'ldapService', 'Registration', 'Login-FB']

def do_auth(user, tree):
    S = requests.Session()
    S.trust_env = False
    S.proxies = {'http': None, 'https': None}
    H = {'User-Agent': 'research-1643',
         'Accept-API-Version': 'resource=1.0, protocol=1.0',
         'Content-Type': 'application/json'}
    url = AUTH
    if tree:
        url += '?authIndexType=service&authIndexValue=' + tree
    r = S.post(url, json={}, timeout=15, verify=False, headers=H)
    d = r.json()
    # 打完整结构(排除长 authId)
    info = {k: v for k, v in d.items() if k != 'authId'}
    print('  init: %d callbacks=%s extra=%s' % (r.status_code,
          [c['type'] for c in d.get('callbacks', [])],
          json.dumps(info)[:200]))
    authId = d.get('authId')
    if not authId:
        return
    for rnd in range(3):
        callbacks = []
        for cb in d.get('callbacks', []):
            t = cb['type']
            inp = []
            if t == 'NameCallback':
                inp = [{'name': 'IDToken1', 'value': user}]
            elif t == 'PasswordCallback':
                inp = [{'name': 'IDToken2', 'value': PASS}]
            elif t == 'ChoiceCallback':
                inp = [{'name': 'IDToken3', 'value': 0}]
            else:
                inp = [{'name': k.get('name'), 'value': ''} for k in cb.get('input', [])]
            callbacks.append({'type': t, 'output': cb.get('output', []), 'input': inp})
        r2 = S.post(url, json={'authId': authId, 'callbacks': callbacks}, timeout=15, verify=False, headers=H)
        d = r2.json()
        if d.get('tokenId'):
            print('  >>> SUCCESS token=%s' % d['tokenId'][:80])
            return d['tokenId']
        extra = {k: v for k, v in d.items() if k not in ('authId',)}
        print('  rnd%d: %d callbacks=%s extra=%s' % (rnd + 1, r2.status_code,
              [c['type'] for c in d.get('callbacks', [])],
              json.dumps(extra)[:250]))
        authId = d.get('authId')
        if not authId:
            print('  final body:', r2.text[:300])
            return None

for user in USER_VARIANTS:
    for tree in TREES:
        print('user=%s tree=%s' % (user, tree))
        do_auth(user, tree)
