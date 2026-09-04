# -*- coding: utf-8 -*-
"""AIC 第六轮:带 Accept-API-Version 规范重测 + authorize 400 详情"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
COOKIE = 'amlbcookie=01; aa942d46ece12ce=IFE9DsM4gWKUGQHkQczCcFOQc8Q.*AAJTSQACMDIAAlNLABxpYlZOOXByMGZQRGNycDhwTGxXS21iZGxDSjA9AAR0eXBlAANDVFMAAlMxAAIwMQ..*'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Cookie': COOKIE,
                  'Accept-API-Version': 'resource=1.0, protocol=1.0'})

def probe(method, path, **kw):
    try:
        r = S.request(method, BASE + path, timeout=12, verify=False, **kw)
        print('%-5s %-70s -> %d  %s' % (method, path, r.status_code, r.text[:300].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-70s -> ERR %s' % (method, path, str(e)[:60]))

print('=== 1. 规范头重测关键端点 ===')
for p in [
    '/am/json/realms/alpha/sessions?_queryFilter=true',
    '/am/json/realms/alpha/users?_queryFilter=true',
    '/am/json/realms/alpha/users/self',
    '/am/json/realms/alpha/applications?_queryFilter=true',
    '/am/json/realms/alpha/selfservice/registration',
    '/am/json/realms/alpha/selfservice/passwordReset',
    '/am/json/realms/alpha/selfservice/userProfile',
    '/am/json/realms/alpha/selfservice/forgotUsername',
    '/am/json/realms/alpha/selfservice/kba',
    '/am/json/realms/alpha/selfservice/terms',
    '/am/json/realms/alpha/selfservice/oauth',
    '/am/json/realms/alpha/users?_action=idFromSession',
]:
    probe('GET', p)

print('\n=== 2. authorize 400 详情 ===')
url = (BASE + '/am/oauth2/alpha/authorize?client_id=endUserUIClient'
       '&response_type=code&scope=fr:iga:*%20openid'
       '&redirect_uri=https%3A%2F%2Fopenam-bug-bounty-stag.forgeblocks.com%2Fenduser%2Fcallback')
r = S.get(url, timeout=12, verify=False, allow_redirects=False)
print('status:', r.status_code)
print('body:', r.text[:600])

print('\n=== 3. 无 redirect_uri 的 authorize(看错误提示) ===')
for q in ['?client_id=endUserUIClient&response_type=code',
          '?client_id=endUserUIClient&response_type=code&scope=fr:iga:*',
          '?client_id=endUserUIClient&response_type=code&scope=openid']:
    r = S.get(BASE + '/am/oauth2/alpha/authorize' + q, timeout=12, verify=False, allow_redirects=False)
    print('%-60s -> %d %s' % (q, r.status_code, r.text[:250].replace('\n', ' ')))
