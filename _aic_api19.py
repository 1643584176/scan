# -*- coding: utf-8 -*-
"""AIC 第三十九轮:Registration 正确提交(保留服务器 input name 只改 value)
修复前两轮客户端 bug。流程:注册 -> 循环提交直到完成 -> 新账户登录/roles/权限对比。
预期结果表:
  成立 -> 注册完成返回 tokenId(或进入验证 stage,打印其类型);新账户权限与 pccp 对比异常点
  不成立 -> 流程在验证 stage 被阻(打印阻止点)
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

def fill_value(cb, username, mail, password):
    """按 callback 类型填值,保留服务器 input name"""
    t = cb['type']
    out_names = [o.get('name') for o in cb.get('output', [])]
    srv_inp = cb.get('input', [])
    vals = []
    for k in srv_inp:
        nm = k.get('name', '')
        if t == 'ValidatedCreateUsernameCallback' and nm == 'IDToken1':
            vals.append({'name': nm, 'value': username})
        elif t == 'ValidatedCreatePasswordCallback' and nm == 'IDToken7':
            vals.append({'name': nm, 'value': password})
        elif t == 'StringAttributeInputCallback':
            field = out_names[0] if out_names else ''
            v = mail if field == 'mail' else ('Reg' if field == 'givenName' else 'Test')
            vals.append({'name': nm, 'value': v if nm.startswith('IDToken') and not nm.endswith('validateOnly') else k.get('value')})
        elif t == 'BooleanAttributeInputCallback':
            vals.append({'name': nm, 'value': True})
        elif t == 'KbaCreateCallback':
            v = "What's your favorite color?" if nm == 'IDToken8question' else 'blue'
            vals.append({'name': nm, 'value': v})
        elif t == 'TermsAndConditionsCallback':
            vals.append({'name': nm, 'value': True})
        else:
            vals.append({'name': nm, 'value': k.get('value')})
    return vals

def run_reg(username, mail):
    print('\n===== 注册 [%s] =====' % username)
    d = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json={},
               timeout=15, verify=False).json()
    for stage in range(1, 8):
        if d.get('tokenId'):
            print('stage %d: !! 注册完成 tokenId=%s' % (stage, d['tokenId'][:40]))
            return d
        if not d.get('authId'):
            print('stage %d: 流程终止' % stage)
            return d
        cbs = d.get('callbacks', [])
        print('stage %d: callbacks=%d %s' % (stage, len(cbs),
              [c['type'] for c in cbs]))
        if not cbs:
            # 无 callbacks 但 authId 在:尝试空提交推进
            body = {'authId': d['authId'], 'callbacks': []}
        else:
            body = {'authId': d['authId'], 'callbacks': [
                {'type': cb['type'], 'output': cb.get('output', []),
                 'input': fill_value(cb, username, mail, 'RegTest1650!x'), '_id': cb.get('_id')}
                for cb in cbs]}
        r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=body,
                   timeout=15, verify=False)
        try:
            d = r.json()
        except Exception:
            print('stage %d: HTTP %d %s' % (stage, r.status_code, r.text[:150]))
            return None
        if r.status_code != 200:
            print('stage %d: HTTP %d %s' % (stage, r.status_code, r.text[:300]))
            return d
        time.sleep(0.3)
    print('超过 7 stage 未完成')
    return d

res = run_reg('regtest1650', 'regtest1650@example.com')

print('\n===== 新账户登录 =====')
r = S.post(AUTH, json={}, timeout=15, verify=False)
d = r.json()
authId = d['authId']
cbs = []
for cb in d.get('callbacks', []):
    t = cb['type']
    inp = [{'name': 'IDToken1', 'value': 'regtest1650'}] if t == 'NameCallback' else \
          [{'name': 'IDToken2', 'value': 'RegTest1650!x'}] if t == 'PasswordCallback' else \
          [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
    cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
try:
    j = r2.json()
    tok2 = j.get('tokenId')
    print('登录 -> %d tokenId=%s' % (r2.status_code, (tok2 or 'NONE')[:30]))
except Exception as e:
    print('登录 -> %d %s' % (r2.status_code, r2.text[:200]))
    tok2 = None

if tok2:
    S2 = requests.Session()
    S2.trust_env = False
    S2.proxies = {'http': None, 'https': None}
    S2.headers.update({'User-Agent': 'research-1643',
                       'Cookie': 'aa942d46ece12ce=' + tok2,
                       'Accept-API-Version': 'resource=2.1, protocol=1.0'})
    # 查自己
    r = S2.get(BASE + '/am/json/realms/root/realms/alpha/users?_queryFilter=userName%20eq%20%22regtest1650%22&_fields=userName,_id,roles,mail',
               timeout=12, verify=False)
    print('新账户查询 -> %d %s' % (r.status_code, r.text[:400].replace('\n', ' ')))
    r = S2.get(BASE + '/am/json/realms/root/realms/alpha/users?_queryFilter=userName%20eq%20%22pccp%22&_fields=userName,_id,roles',
               timeout=12, verify=False)
    print('pccp 对照查询 -> %d %s' % (r.status_code, r.text[:300].replace('\n', ' ')))
