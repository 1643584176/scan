# -*- coding: utf-8 -*-
"""AIC 第五十七轮-恢复脚本:B 段已把 pccp 密码改为 NEWPASS,立即改回
1. 用 NEWPASS 登录(新会话,验证当前密码)
2. changePassword: currentpassword=NEWPASS, userpassword=原密码
3. 用原密码登录验证恢复
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
COOKIE_NAME = 'aa942d46ece12ce'
NEWPASS = 'PccpChanged2026!x'

def fresh_login(u, p):
    s = requests.Session()
    s.trust_env = False
    s.proxies = {'http': None, 'https': None}
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    r = s.post(AUTH, json={}, timeout=15, verify=False)
    try:
        d = r.json()
    except Exception:
        return None, r.status_code, r.text[:200]
    if 'authId' not in d:
        return None, r.status_code, json.dumps(d)[:200]
    cbs = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        inp = [{'name': 'IDToken1', 'value': u}] if t == 'NameCallback' else \
              [{'name': 'IDToken2', 'value': p}] if t == 'PasswordCallback' else \
              [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
        cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
    r2 = s.post(AUTH, json={'authId': d['authId'], 'callbacks': cbs}, timeout=15, verify=False)
    try:
        return r2.json().get('tokenId'), r2.status_code, r2.text[:200]
    except Exception:
        return None, r2.status_code, r2.text[:200]

print('=== 1. NEWPASS 登录验证 ===')
tok, code, body = fresh_login(USER, NEWPASS)
print('NEWPASS 登录 -> %s (HTTP %d %s)' % ('SUCCESS' if tok else 'FAIL', code, body))
if not tok:
    tok2, code2, body2 = fresh_login(USER, PASS)
    print('原密码登录(判断 B 段是否生效)-> %s (HTTP %d %s)' % ('SUCCESS' if tok2 else 'FAIL', code2, body2))
    if tok2:
        print('B 段未生效,账号正常')
        raise SystemExit(0)

print('\n=== 2. changePassword 改回原密码 ===')
s = requests.Session()
s.trust_env = False
s.proxies = {'http': None, 'https': None}
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Cookie': COOKIE_NAME + '=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
r = s.post(BASE + '/am/json/realms/root/realms/alpha/users/%s?_action=changePassword' % MY_ID,
           json={'currentpassword': NEWPASS, 'userpassword': PASS}, timeout=15, verify=False)
print('改回 -> HTTP %d %s' % (r.status_code, r.text[:200]))

print('\n=== 3. 原密码登录验证 ===')
tok3, code3, body3 = fresh_login(USER, PASS)
print('原密码登录 -> %s (HTTP %d %s)' % ('SUCCESS' if tok3 else 'FAIL', code3, body3))
