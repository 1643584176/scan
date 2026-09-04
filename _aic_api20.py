# -*- coding: utf-8 -*-
"""AIC 第四十轮:Registration 提交诊断 2——对比提交前后 callbacks 差异
前两轮提交均返回相同 9 callbacks。本轮 dump 提交前/后两套 callbacks,
   对比 failedPolicies/value 回显/结构差异,定位服务器为什么不接受。
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
OUT = open('D:/scan/_aic_api20_dump.json', 'w', encoding='utf-8')

def log(tag, obj):
    OUT.write('\n===== %s =====\n%s\n' % (tag, json.dumps(obj, ensure_ascii=False, indent=1)))
    OUT.flush()

# 启动
r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json={}, timeout=15, verify=False)
d0 = r.json()
log('启动', d0)
cbs = d0['callbacks']

def make_submit(d, username, mail, password):
    body_cbs = []
    for cb in d['callbacks']:
        t = cb['type']
        out_names = [o.get('name') for o in cb.get('output', [])]
        srv = cb.get('input', [])
        new_inp = []
        for k in srv:
            nm = k.get('name', '')
            if t == 'ValidatedCreateUsernameCallback' and nm == 'IDToken1':
                new_inp.append({'name': nm, 'value': username})
            elif t == 'ValidatedCreatePasswordCallback' and nm == 'IDToken7':
                new_inp.append({'name': nm, 'value': password})
            elif t == 'StringAttributeInputCallback':
                # 字段名在 output 中 name='name' 的 value 里(givenName/sn/mail)
                field = ''
                for o in cb.get('output', []):
                    if o.get('name') == 'name':
                        field = o.get('value', '')
                        break
                v = mail if field == 'mail' else ('Reg' if field == 'givenName' else 'Test')
                if nm.endswith('validateOnly'):
                    new_inp.append({'name': nm, 'value': False})
                else:
                    new_inp.append({'name': nm, 'value': v})
            elif t == 'BooleanAttributeInputCallback':
                if nm.endswith('validateOnly'):
                    new_inp.append({'name': nm, 'value': False})
                else:
                    new_inp.append({'name': nm, 'value': True})
            elif t == 'KbaCreateCallback':
                v = "What's your favorite color?" if nm == 'IDToken8question' else 'blue'
                new_inp.append({'name': nm, 'value': v})
            elif t == 'TermsAndConditionsCallback':
                new_inp.append({'name': nm, 'value': True})
            else:
                new_inp.append({'name': nm, 'value': k.get('value')})
        body_cbs.append({'type': t, 'output': cb.get('output', []), 'input': new_inp, '_id': cb.get('_id')})
    return {'authId': d['authId'], 'callbacks': body_cbs}

body = make_submit(d0, 'regdiag1651', 'regdiag1651@example.com', 'RegTest1651!x')
log('提交 body', body)
r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=body, timeout=15, verify=False)
d1 = r.json()
log('提交1 响应', d1)
print('提交1 -> %d, callbacks=%d' % (r.status_code, len(d1.get('callbacks', []))))

# 对比:每个 callback 的 output 差异
for i, (cb0, cb1) in enumerate(zip(cbs, d1.get('callbacks', []))):
    t0, t1 = cb0['type'], cb1['type']
    # failedPolicies 对比
    fp0 = [o for o in cb0.get('output', []) if o.get('name') == 'failedPolicies']
    fp1 = [o for o in cb1.get('output', []) if o.get('name') == 'failedPolicies']
    v0 = [o for o in cb0.get('output', []) if o.get('name') == 'value']
    v1 = [o for o in cb1.get('output', []) if o.get('name') == 'value']
    diff = []
    if fp0 != fp1:
        diff.append('failedPolicies: %s -> %s' % (json.dumps(fp0), json.dumps(fp1)[:200]))
    if v0 != v1:
        diff.append('value: %s -> %s' % (json.dumps(v0)[:100], json.dumps(v1)[:100]))
    if t0 != t1:
        diff.append('type: %s -> %s' % (t0, t1))
    if not diff:
        diff.append('(无差异)')
    print('[%d] %s: %s' % (i, t0, ' | '.join(diff)))

OUT.close()
print('\ndump -> _aic_api20_dump.json')
