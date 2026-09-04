# -*- coding: utf-8 -*-
"""AIC 第十三轮:1) 授权码流 token 详情 2) 新 token 写入测试(PATCH 自己资料/属性篡改)
预期结果表:
  成立 -> token 只有配置的 scope;PATCH 只能改白名单属性;roles 等受保护属性被拒
  不成立(发现) -> PATCH 可改 roles/memberOf/admin 属性(提权)
"""
import requests, urllib3, json, base64
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

def get_token(scope):
    url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
           '&response_type=code&redirect_uri=%s&scope=%s&state=test123' % (RU, scope))
    r = S.get(url, timeout=12, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    if 'code=' not in loc:
        return None, 'no code: ' + loc[:100]
    code = loc.split('code=')[1].split('&')[0]
    r2 = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
                data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU},
                timeout=12, verify=False)
    return r2.status_code, r2.text[:600]

print('=== 1. 授权码流 token 详情 ===')
for scope in ['openid fr:iga:*', 'openid fr:idm:*']:
    st, body = get_token(scope)
    print('\nscope=%s -> %s' % (scope, st))
    print(body)
    try:
        j = json.loads(body)
        tok = j.get('access_token', '')
        if tok:
            p = tok.split('.')[1]
            p += '=' * (-len(p) % 4)
            print('payload scope:', json.loads(base64.urlsafe_b64decode(p)).get('scope'))
    except Exception as e:
        print('parse:', e)
