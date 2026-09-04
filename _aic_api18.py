# -*- coding: utf-8 -*-
"""AIC 第三十八轮:Registration 提交诊断——完整 dump 每 stage 响应
上轮循环提交 6 stage 均返回新 authId,但 callbacks 详情被截断。
本轮 dump 完整 JSON 到文件细看:每次提交后返回什么 callbacks/错误字段。
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
OUT = open('D:/scan/_aic_api18_dump.json', 'w', encoding='utf-8')

def log(tag, obj):
    OUT.write('\n===== %s =====\n%s\n' % (tag, json.dumps(obj, ensure_ascii=False, indent=1)))
    OUT.flush()

# 启动
r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json={}, timeout=15, verify=False)
d = r.json()
log('启动树', d)
print('启动:', r.status_code, 'authId?', bool(d.get('authId')), 'callbacks:', len(d.get('callbacks', [])))
cbs = d.get('callbacks', [])

# 构造第一轮提交
inp_map = {}
for cb in cbs:
    t = cb['type']
    out_names = [o.get('name') for o in cb.get('output', [])]
    if t == 'ValidatedCreateUsernameCallback':
        inp_map[id(cb)] = [{'name': 'username', 'value': 'regdiag1648'}]
    elif t == 'ValidatedCreatePasswordCallback':
        inp_map[id(cb)] = [{'name': 'password', 'value': 'RegTest1648!x'}]
    elif t == 'StringAttributeInputCallback':
        nm = out_names[0] if out_names else 'value'
        val = 'regdiag1648@example.com' if nm == 'mail' else ('Reg' if nm == 'givenName' else 'Test')
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
body = {'authId': d['authId'], 'callbacks': [
    {'type': cb['type'], 'output': cb.get('output', []), 'input': inp_map[id(cb)], '_id': cb.get('_id')}
    for cb in cbs]}
log('提交1 body', body)

r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration', json=body, timeout=15, verify=False)
d2 = r.json()
log('提交1 响应', d2)
print('提交1:', r.status_code, 'authId?', bool(d2.get('authId')), 'tokenId?', bool(d2.get('tokenId')),
      'callbacks:', len(d2.get('callbacks', [])), 'err:', d2.get('errorMessage'), d2.get('message'))
if d2.get('callbacks'):
    for i, cb in enumerate(d2['callbacks']):
        log('提交1 cb%d' % i, cb)

# 第二次:用新 authId + 空 callbacks
if d2.get('authId'):
    r = S.post(AUTH + '?authIndexType=service&authIndexValue=Registration',
               json={'authId': d2['authId'], 'callbacks': []}, timeout=15, verify=False)
    d3 = r.json()
    log('提交2(空cbs)', d3)
    print('提交2:', r.status_code, 'authId?', bool(d3.get('authId')), 'tokenId?', bool(d3.get('tokenId')),
          'callbacks:', len(d3.get('callbacks', [])), 'err:', d3.get('errorMessage'), d3.get('message'))
    if d3.get('callbacks'):
        for i, cb in enumerate(d3['callbacks']):
            log('提交2 cb%d' % i, cb)

OUT.close()
print('\ndump 完成 -> _aic_api18_dump.json')
