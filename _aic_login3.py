# -*- coding: utf-8 -*-
"""AIC 登录变体:不同 header 组合 + enduser 认证树名猜测"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER = '1643584176@qq.com'
PASS = 'Agent360User$5h2!QxR'

HEADER_VARIANTS = [
    {},  # 基线
    {'X-Requested-With': 'XMLHttpRequest'},
    {'X-Requested-With': 'XMLHttpRequest', 'X-OpenAM-Username': USER},
    {'X-Requested-With': 'ForgeRock-CRM'},
]
TREES = [None, 'Login', 'EndUserLogin', 'UserLogin', 'EndUser']

def attempt(headers_extra, tree):
    S = requests.Session()
    S.trust_env = False
    S.proxies = {'http': None, 'https': None}
    H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         'Accept-API-Version': 'resource=1.0, protocol=1.0',
         'Content-Type': 'application/json'}
    H.update(headers_extra)
    url = AUTH
    if tree:
        url += '?authIndexType=service&authIndexValue=' + tree
    try:
        r = S.post(url, json={}, timeout=15, verify=False, headers=H)
        d = r.json()
        authId = d.get('authId')
        if not authId:
            return 'init-fail %s' % r.text[:120]
        cbs = []
        for cb in d.get('callbacks', []):
            t = cb['type']
            inp = []
            if t == 'NameCallback':
                inp = [{'name': 'IDToken1', 'value': USER}]
            elif t == 'PasswordCallback':
                inp = [{'name': 'IDToken2', 'value': PASS}]
            else:
                inp = [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
            cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
        r2 = S.post(url, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False, headers=H)
        d2 = r2.json()
        if d2.get('tokenId'):
            return 'SUCCESS ' + d2['tokenId'][:60]
        cbt = [c['type'] for c in d2.get('callbacks', [])]
        msg = [o.get('value') for c in d2.get('callbacks', []) for o in c.get('output', []) if o.get('name') == 'message']
        return 'cb=%s msg=%s' % (cbt, msg[:1])
    except Exception as e:
        return 'ERR ' + str(e)[:80]

for h_i, he in enumerate(HEADER_VARIANTS):
    for t in TREES:
        r = attempt(he, t)
        tag = ('hdr%d' % h_i) if he else 'base'
        print('%-6s tree=%-10s -> %s' % (tag, t or '-', r))
