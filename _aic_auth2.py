# -*- coding: utf-8 -*-
"""AIC 第四轮(修订):用浏览器会话 cookie 测授权面
cookie: amlbcookie=01; aa942d46ece12ce=<OpenAM session token>
预期结果表:
  成立 -> 只有自己的数据可见;其他用户资源 403/404;管理端点拒绝
  不成立(发现) -> 可枚举/访问其他用户数据、管理端点、跨 realm 数据
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=IFE9DsM4gWKUGQHkQczCcFOQc8Q.*AAJTSQACMDIAAlNLABxpYlZOOXByMGZQRGNycDhwTGxXS21iZGxDSjA9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Cookie': COOKIE})

def probe(method, path, **kw):
    try:
        r = S.request(method, BASE + path, timeout=12, verify=False, **kw)
        body = r.text[:400].replace('\n', ' ')
        print('%-5s %-68s -> %d  %s' % (method, path, r.status_code, body))
        return r
    except Exception as e:
        print('%-5s %-68s -> ERR %s' % (method, path, str(e)[:60]))

print('=== 1. 会话有效性 ===')
probe('GET', '/am/json/realms/alpha/sessions?_action=getSessionInfo')
probe('GET', '/am/oauth2/alpha/userinfo')

print('\n=== 2. 用户资源(基线) ===')
probe('GET', '/am/json/realms/alpha/users?_queryFilter=true')
probe('GET', '/am/json/realms/alpha/users/self')

print('\n=== 3. 管理/越权探测 ===')
for p in [
    '/am/json/realms/alpha/users?_queryFilter=userName+sw+"researcher"',
    '/am/json/realms/alpha/users?_queryFilter=mail+sw+"1643584176"',
    '/am/json/realms/alpha/users?_queryFilter=true&_pageSize=100',
    '/am/json/realms/root/users?_queryFilter=true',
    '/am/json/realms/alpha/groups?_queryFilter=true',
    '/am/json/realms/alpha/realms',
    '/am/json/realms/alpha/realm-config',
    '/am/json/realms/alpha/applications?_queryFilter=true',
    '/am/json/realms/alpha/agents?_queryFilter=true',
    '/am/json/realms/alpha/policies?_queryFilter=true',
    '/am/json/realms/alpha/devices?_queryFilter=true',
    '/am/json/realms/alpha/oauth2/clients?_queryFilter=true',
    '/am/json/realms/alpha/sessions?_queryFilter=true',
    '/am/json/realms/alpha/sessions?_action=logout',
    '/am/oauth2/alpha/introspect',
    '/openidm/managed/user?_queryFilter=true',
    '/openidm/managed/user/db3d6356-61a0-4684-9eaa-c1353dfa44d9',
    '/iga/rest/roles',
    '/iga/rest/accesses',
]:
    probe('GET', p)
