# -*- coding: utf-8 -*-
"""AIC 第十一轮:1) /iga/governance/ 端点枚举 2) 正确路径(/realms/root/realms/alpha + 2.1)重测
预期结果表:
  成立 -> 未授权端点 403/404;sessions getSessionInfo 只返回自己会话
  不成立(发现) -> 暴露未预期端点(approvals/violations/roles 等管理面)/返回他人数据
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJjdHMiOiJPQVVUSDJfU1RBVEVMRVNTX0dSQU5UIiwiYXV0aF9sZXZlbCI6MCwiYXVkaXRUcmFja2luZ0lkIjoiZWFiYWVmY2UtODJkZi00NDYyLTkwZTctMTk1YmZkNTAwMDQ1LTM4ODY2NyIsInN1Ym5hbWUiOiJkYjNkNjM1Ni02MWEwLTQ2ODQtOWVhYS1jMTM1M2RmYTQ0ZDkiLCJpc3MiOiJodHRwczovL29wZW5hbS1idWctYm91bnR5LXN0YWcuZm9yZ2VibG9ja3MuY29tOjQ0My9hbS9vYXV0aDIvYWxwaGEiLCJ0b2tlbk5hbWUiOiJhY2Nlc3NfdG9rZW4iLCJ0b2tlbl90eXBlIjoiQmVhcmVyIiwiYXV0aEdyYW50SWQiOiIzS2lQN0tPNTdhU2hhb0RXZkE3SG9nbmNkbEUiLCJjbGllbnRfaWQiOiJlbmRVc2VyVUlDbGllbnQiLCJhdWQiOiJlbmRVc2VyVUlDbGllbnQiLCJuYmYiOjE3ODgyNDc4NzIsImdyYW50X3R5cGUiOiJhdXRob3JpemF0aW9uX2NvZGUiLCJzY29wZSI6WyJmcjppZ2E6KiJdLCJhdXRoX3RpbWUiOjE3ODgyNDc4NjUsInJlYWxtIjoiL2FscGhhIiwiZXhwIjoxNzg4MjUxNDcyLCJpYXQiOjE3ODgyNDc4NzIsImV4cGlyZXNfaW4iOjM2MDAsImp0aSI6IlczV1BMbG91TTZFRVhiX1plZjFiSThzX3c4byIsImdyb3VwcyI6W119.fplQO_Jk7Z8jdecHJWMY5KLrZl_eZikklLXNHYOlJV4'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=tvVfNxaXuVbrr2BzbooZZTz8iTk.*AAJTSQACMDIAAlNLABxZNXdTYkVsVmxPdWdiRlZkeDc3V3doNTJ1VTg9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Authorization': 'Bearer ' + TOKEN,
                  'Cookie': COOKIE,
                  'Content-Type': 'application/json',
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})

def probe(method, path, body=None):
    try:
        kw = {}
        if body is not None:
            kw['json'] = body
        r = S.request(method, BASE + path, timeout=12, verify=False, **kw)
        print('%-5s %-78s -> %d  %s' % (method, path[:78], r.status_code, r.text[:200].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-78s -> ERR %s' % (method, path[:78], str(e)[:60]))

print('=== 1. IGA governance 子树枚举 ===')
for p in [
    '/iga/governance/user/%s' % MY_ID,
    '/iga/governance/user/%s/roles' % MY_ID,
    '/iga/governance/user/%s/accesses' % MY_ID,
    '/iga/governance/user/%s/approvals' % MY_ID,
    '/iga/governance/user/%s/violations' % MY_ID,
    '/iga/governance/user/%s/certifications' % MY_ID,
    '/iga/governance/user/%s/entitlements' % MY_ID,
    '/iga/governance/user/%s/assignments' % MY_ID,
    '/iga/governance/user/%s/requests' % MY_ID,
    '/iga/governance/roles',
    '/iga/governance/roles?pageSize=10',
    '/iga/governance/accesses',
    '/iga/governance/approvals',
    '/iga/governance/approvals?pageSize=10',
    '/iga/governance/violations',
    '/iga/governance/policies',
    '/iga/governance/applications',
    '/iga/governance/groups',
    '/iga/governance/users',
    '/iga/governance/users?pageSize=10',
    '/iga/governance/me',
    '/iga/governance/me/grants',
    '/iga/governance/me/roles',
    '/iga/governance/me/accesses',
    '/iga/governance/me/approvals',
    '/iga/governance/me/violations',
    '/iga/governance/me/requests',
    '/iga/governance/me/requests?_action=search',
]:
    probe('GET', p)

print('\n=== 2. 正确路径重测(2.1) ===')
probe('POST', '/am/json/realms/root/realms/alpha/sessions?_action=getSessionInfo', {'withCredentials': True})
probe('GET', '/am/json/realms/root/realms/alpha/users?_queryFilter=true')
probe('GET', '/am/json/realms/root/realms/alpha/users/self')
probe('GET', '/am/json/realms/root/realms/alpha/applications?_queryFilter=true')
probe('GET', '/am/json/realms/root/realms/alpha/realm-config')
probe('GET', '/am/json/realms/root/realms/alpha/selfservice/kba')
probe('GET', '/am/json/realms/root/realms/alpha/groups?_queryFilter=true')
probe('GET', '/am/json/realms/root/realms/alpha/agents?_queryFilter=true')
probe('GET', '/am/json/realms/root/realms/alpha/policies?_queryFilter=true')
