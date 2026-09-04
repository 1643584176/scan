# -*- coding: utf-8 -*-
"""AIC 第二十九轮:全小写字段名验证——changePassword/mail 修改的 currentpassword 校验
1. changePassword:{userpassword, currentpassword}——正确/错误/空/缺失校验对比
2. mail 修改:{mail, currentpassword}——正确/错误/空
3. 改密后旧会话是否失效(会话管理)
4. endSession logout 开放重定向
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
ORIG_MAIL = '1643584176@qq.com'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
                  'Content-Type': 'application/json'})
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
S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
tok = S.cookies.get('aa942d46ece12ce')
print('LOGIN OK')

S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'research-1643', 'Cookie': 'aa942d46ece12ce=' + tok,
                   'Content-Type': 'application/json', 'Accept-API-Version': 'resource=2.1, protocol=1.0'})

U = '/am/json/realms/root/realms/alpha/users/' + MY_ID

def probe(method, path, body=None, label=''):
    kw = {'timeout': 12, 'verify': False}
    if body is not None:
        kw['json'] = body
    try:
        r = S2.request(method, BASE + path, **kw)
        tag = ('  <= ' + label) if label else ''
        print('%-5s %-60s -> %d  %s%s' % (method, path[:60], r.status_code, r.text[:240].replace('\n', ' '), tag))
        return r
    except Exception as e:
        print('%-5s %-60s -> ERR %s' % (method, path[:60], str(e)[:60]))

def login_as(u, p):
    S3 = requests.Session()
    S3.trust_env = False
    S3.proxies = {'http': None, 'https': None}
    S3.headers.update({'User-Agent': 'x', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
                       'Content-Type': 'application/json'})
    try:
        r = S3.post(AUTH, json={}, timeout=12, verify=False)
        d = r.json()
        cbs = []
        for cb in d.get('callbacks', []):
            t = cb['type']
            inp = [{'name': 'IDToken1', 'value': u}] if t == 'NameCallback' else \
                  [{'name': 'IDToken2', 'value': p}] if t == 'PasswordCallback' else \
                  [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
            cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
        r2 = S3.post(AUTH, json={'authId': d['authId'], 'callbacks': cbs}, timeout=12, verify=False)
        return r2.status_code, bool(r2.json().get('tokenId'))
    except Exception:
        return 0, False

print('=== 1. changePassword(全小写字段) ===')
probe('POST', U + '?_action=changePassword', {'userpassword': 'Temp1643$!', 'currentpassword': PASS}, '正确 currentpassword')
print('  temp 登录:', login_as(USER, 'Temp1643$!'))
probe('POST', U + '?_action=changePassword', {'userpassword': 'Temp1643$!', 'currentpassword': 'WRONGPASS'}, '错误 currentpassword')
print('  错误后 temp 登录:', login_as(USER, 'Temp1643$!'))
probe('POST', U + '?_action=changePassword', {'userpassword': 'Temp1643$!', 'currentpassword': ''}, '空 currentpassword')
print('  空后 temp 登录:', login_as(USER, 'Temp1643$!'))
# 恢复(若 temp 生效)
if login_as(USER, 'Temp1643$!')[1]:
    probe('POST', U + '?_action=changePassword', {'userpassword': PASS, 'currentpassword': 'Temp1643$!'}, '恢复原密码')
    print('  恢复后原密码登录:', login_as(USER, PASS))
else:
    print('  (密码未改)')

print('\n=== 2. mail 修改(currentpassword) ===')
for body, lab in [
    ({'mail': 't1643@test.com', 'currentpassword': PASS}, '正确 currentpassword'),
    ({'mail': 't1643@test.com', 'currentpassword': 'WRONGPASS'}, '错误 currentpassword'),
    ({'mail': 't1643@test.com', 'currentpassword': ''}, '空 currentpassword'),
]:
    r = probe('PUT', U, body, 'mail+' + lab)
    r2 = S2.get(BASE + U, timeout=12, verify=False)
    cur = r2.json().get('mail') if r2.status_code == 200 else '?'
    print('  当前 mail:', cur)
    if cur == ['t1643@test.com']:
        print('  [发现] mail 修改生效!恢复...')
        probe('PUT', U, {'mail': ORIG_MAIL, 'currentpassword': PASS}, '恢复 mail')
        break

print('\n=== 3. 改密后旧会话有效性 ===')
# 3a: 修改密码(用 temp)
r = probe('POST', U + '?_action=changePassword', {'userpassword': 'Temp1643$!', 'currentpassword': PASS}, '改密 temp')
# 3b: 旧会话 S2 还能用吗(getSessionInfo)
r = S2.post(BASE + '/am/json/realms/root/realms/alpha/sessions?_action=getSessionInfo',
            json={'withCredentials': True}, timeout=12, verify=False)
print('改密后旧会话 getSessionInfo:', r.status_code, r.text[:150].replace('\n', ' '))
# 3c: 恢复密码
probe('POST', U + '?_action=changePassword', {'userpassword': PASS, 'currentpassword': 'Temp1643$!'}, '恢复原密码')
print('  恢复后原密码登录:', login_as(USER, PASS))

print('\n=== 4. endSession logout 开放重定向 ===')
from urllib.parse import quote
for ru, lab in [
    ('https://evil.com', '外域'),
    ('https://openam-bug-bounty-stag.forgeblocks.com.evil.com', '域名后缀'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/', '同源'),
    ('', '空'),
]:
    p = '/am/oauth2/realms/alpha/connect/endSession?post_logout_redirect_uri=%s' % quote(ru, safe='')
    try:
        r = S.get(BASE + p, timeout=12, verify=False, allow_redirects=False)
        print('endSession %-20s -> %d %s' % (lab, r.status_code, r.headers.get('Location', '')[:150]))
    except Exception as e:
        print('endSession %-20s -> ERR %s' % (lab, str(e)[:50]))
