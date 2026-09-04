# -*- coding: utf-8 -*-
"""AIC 第三十七轮:Registration 树多 stage 循环提交(直到完成)
上轮发现:首轮提交返回新 authId(流程继续)。本轮回环提交直到 tokenId/结束,
   观察每 stage 的 callbacks 变化与最终错误信息(用户名唯一性校验时机/枚举)。
预期结果表:
  成立 -> 注册完成(无邮件验证)返回 tokenId;新账户可登录;重复用户名在完成时报错泄露存在性
  不成立 -> 流程需要邮件验证码等额外 stage(打印出阻止点)
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

def summarize(d):
    out = {'authId': d.get('authId'), 'tokenId': d.get('tokenId'), 'successUrl': d.get('successUrl')}
    cbs = d.get('callbacks', [])
    out['n_callbacks'] = len(cbs)
    out['cb_types'] = [c['type'] for c in cbs]
    return out

def build_inputs(cbs, username, mail, password='RegTest1644!x', fresh=True):
    """为当前 stage 的 callbacks 构造 input;后续 stage 若无 callbacks 返回 []"""
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
    return [{'type': cb['type'], 'output': cb.get('output', []),
             'input': inp_map[id(cb)], '_id': cb.get('_id')} for cb in cbs]

def run_reg(username, mail):
    print('\n===== 注册 [%s] 循环提交 =====' % username)
    d = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json={},
               timeout=15, verify=False).json()
    for stage in range(1, 7):
        info = summarize(d)
        print('stage %d -> %s' % (stage, json.dumps(info, ensure_ascii=False)[:220]))
        if d.get('tokenId'):
            print('  !! 注册完成 tokenId:', d['tokenId'][:40])
            return d
        if not d.get('authId'):
            print('  !! 流程终止(无 authId)')
            return d
        cbs = d.get('callbacks', [])
        body = {'authId': d['authId'], 'callbacks': build_inputs(cbs, username, mail)}
        r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=body,
                   timeout=15, verify=False)
        try:
            d = r.json()
        except Exception:
            print('  stage %d -> HTTP %d %s' % (stage, r.status_code, r.text[:150]))
            return None
        if r.status_code != 200:
            print('  stage %d -> HTTP %d %s' % (stage, r.status_code, r.text[:250]))
            return d
        time.sleep(0.3)
    print('  !! 超过 6 stage 未完成')
    return d

print('--- 1. 正常注册 regtest1646 ---')
res = run_reg('regtest1646', 'regtest1646@example.com')

print('\n--- 2. 重复用户名 pccp(唯一性校验时机) ---')
res2 = run_reg('pccp', 'pccp-newmail@example.com')

print('\n--- 3. 重复邮箱(regtest1646 的邮箱) ---')
res3 = run_reg('regtest1647', 'regtest1646@example.com')
