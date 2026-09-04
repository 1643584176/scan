# -*- coding: utf-8 -*-
"""AIC 第四轮:用 enduser UI 的 access token(fr:iga:*)测授权面
预期结果表:
  成立 -> userinfo 只返回自己的子集;受保护端点按 scope 判定;其他用户资源 403/404
  不成立(发现) -> 可访问其他用户数据 / 管理端点 / 未授权 scope 的资源
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJjdHMiOiJPQVVUSDJfU1RBVEVMRVNTX0dSQU5UIiwiYXV0aF9sZXZlbCI6MCwiYXVkaXRUcmFja2luZ0lkIjoiZWFiYWVmY2UtODJkZi00NDYyLTkwZTctMTk1YmZkNTAwMDQ1LTM4MjM0NyIsInN1Ym5hbWUiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJpc3MiOiJodHRwczovL29wZW5hbS1idWctYm91bnR5LXN0YWcuZm9yZ2VibG9ja3MuY29tOjQ0My9hbS9vYXV0aDIvYWxwaGEiLCJ0b2tlbk5hbWUiOiJhY2Nlc3NfdG9rZW4iLCJ0b2tlbl90eXBlIjoiQmVhcmVyIiwiYXV0aEdyYW50SWQiOiJVYUIyUWNQX3dwU2t6cmU0bC10d3ZjSURreTAiLCJjbGllbnRfaWQiOiJlbmRVc2VyVUlDbGllbnQiLCJhdWQiOiJlbmRVc2VyVUlDbGllbnQiLCJuYmYiOjE3ODgyNDY1OTUsImdyYW50X3R5cGUiOiJhdXRob3JpemF0aW9uX2NvZGUiLCJzY29wZSI6WyJmcjppZ2E6KiJdLCJhdXRoX3RpbWUiOjE3ODgyNDY1ODcsInJlYWxtIjoiL2FscGhhIiwiZXhwIjoxNzg4MjUwMTk1LCJpYXQiOjE3ODgyNDY1OTUsImV4cGlyZXNfaW4iOjM2MDAsImp0aSI6Im54WXJianEtdkdQa1Jsc2FuWG93SmhvV3ZTRSIsImdyb3VwcyI6W119._4EIOc5evmBSUGcyv7wSAK128-knivuBZHGSYm9XO0s'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Authorization': 'Bearer ' + TOKEN})

# 保存 token 备用
with open(r'D:\scan\_aic_token.txt', 'w') as f:
    f.write(TOKEN)

def probe(method, path, **kw):
    try:
        r = S.request(method, BASE + path, timeout=12, verify=False, **kw)
        body = r.text[:400]
        print('%-6s %-70s -> %d  %s' % (method, path, r.status_code, body.replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-6s %-70s -> ERR %s' % (method, path, str(e)[:60]))

print('=== 1. userinfo(基线) ===')
probe('GET', '/am/oauth2/alpha/userinfo')

print('\n=== 2. enduser 相关 API 面 ===')
for p in [
    '/am/json/realms/alpha/users/self',
    '/am/json/realms/alpha/users?_queryFilter=true',
    '/am/json/realms/alpha/sessions?_action=getSessionInfo',
    '/am/json/realms/alpha/selfservice/userProfile',
    '/am/json/realms/alpha/authenticate',
    '/am/oauth2/alpha/introspect',
    '/am/oauth2/alpha/connect/checkSession',
    '/am/enduser/rest/security/authenticated',
    '/am/enduser/rest/security/user',
    '/am/enduser/rest/profile',
    '/iga/rest/accesses',
    '/iga/rest/assignments',
    '/iga/rest/roles',
    '/iga/api/roles',
    '/openidm/enduser/self',
    '/openidm/managed/user/db3d6356-61a0-4684-9eaa-c1353dfa44d9',
    '/openidm/managed/user?_queryFilter=true',
    '/openidm/system/ldap/user?_queryFilter=true',
]:
    probe('GET', p)
