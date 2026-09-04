# -*- coding: utf-8 -*-
"""AIC 第二轮:OIDC discovery 全量 + authenticate callbacks + isAlive 内容
预期结果表:
  成立 -> discovery 只含标准字段;authenticate 无认证返回 callbacks 数组;isAlive 只回 'true'
  不成立(发现) -> discovery 含内部主机/密钥/多余端点;authenticate 直接返回 tokenId(未认证即会话);isAlive 泄露版本/堆栈
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers['User-Agent'] = 'research-1643'

print('=== 1. OIDC discovery (alpha realm) ===')
r = S.get(BASE + '/am/oauth2/realms/alpha/.well-known/openid-configuration', timeout=12, verify=False)
print('status:', r.status_code)
try:
    j = r.json()
    for k in sorted(j):
        v = j[k]
        if isinstance(v, (list, dict)):
            print('  %-35s %s' % (k, json.dumps(v)[:300]))
        else:
            print('  %-35s %s' % (k, str(v)[:200]))
except Exception as e:
    print('not json:', r.text[:300])

print()
print('=== 2. authenticate POST (callbacks) ===')
for body in [None, {}, {'authId': ''}]:
    try:
        r = S.post(BASE + '/am/json/realms/alpha/authenticate', json=body,
                   timeout=12, verify=False,
                   headers={'Accept-API-Version': 'resource=1.0, protocol=1.0'})
        print('body=%s -> %d' % (body, r.status_code))
        print(r.text[:500])
        print('---')
    except Exception as e:
        print('ERR', str(e)[:80])

print()
print('=== 3. isAlive.jsp ===')
r = S.get(BASE + '/am/isAlive.jsp', timeout=12, verify=False)
print(r.status_code, repr(r.text[:200]))

print()
print('=== 4. 401 响应细节 (users) ===')
r = S.get(BASE + '/am/json/realms/alpha/users', timeout=12, verify=False)
print('WWW-Authenticate:', r.headers.get('WWW-Authenticate'))
print('body:', r.text[:300])
