# -*- coding: utf-8 -*-
"""AIC 第十九轮:API 登录会话 cookie 名探测
线索:浏览器 cookie 值 == tokenId 格式,但 iPlanetDirectoryPro header/cookie 全 401
假设:登录响应 Set-Cookie 含真实 cookie 名(AIC 自定义)
验证:拿到 cookie 名后,用 tokenId 作为 cookie 值访问会话端点
预期结果表:
  成立 -> API 登录能建立与浏览器等价的会话(cookie 名+tokenId 可访问 getSessionInfo)
  不成立 -> API 登录只返回纸面 tokenId,会话必须由浏览器建立(API 会话禁用)
"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'research-1643',
                  'Accept-API-Version': 'resource=1.0, protocol=1.0',
                  'Content-Type': 'application/json'})

r = S.post(AUTH, json={}, timeout=15, verify=False)
d = r.json()
authId = d.get('authId')
print('init:', r.status_code, [c['type'] for c in d.get('callbacks', [])])

callbacks = []
for cb in d.get('callbacks', []):
    t = cb['type']
    inp = [{'name': 'IDToken1', 'value': USER}] if t == 'NameCallback' else \
          [{'name': 'IDToken2', 'value': PASS}] if t == 'PasswordCallback' else \
          [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
    callbacks.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})

r2 = S.post(AUTH, json={'authId': authId, 'callbacks': callbacks}, timeout=15, verify=False)
d2 = r2.json()
tok = d2.get('tokenId')
print('login:', r2.status_code, 'token:', (tok or '')[:50])

print('\n=== 登录响应 Set-Cookie(真实 cookie 名) ===')
for k, v in r2.headers.items():
    if k.lower() in ('set-cookie', 'set-cookie2', 'location'):
        print('  %s: %s' % (k, v[:300]))

print('\n=== 登录后 S.cookies(requests 自动收集) ===')
for c in S.cookies:
    print('  %s=%s (domain=%s path=%s secure=%s httponly=%s)' % (c.name, c.value[:60], c.domain, c.path, c.secure, c.has_nonstandard_attr('HttpOnly') if hasattr(c, 'has_nonstandard_attr') else '?'))

print('\n=== 全 header 响应(前 30 个) ===')
for i, (k, v) in enumerate(list(r2.headers.items())[:30]):
    print('  %s: %s' % (k, v[:200]))

if not tok:
    raise SystemExit('no token')

print('\n=== 用 tokenId 做各种认证尝试 ===')

def try_auth(desc, headers):
    S2 = requests.Session()
    S2.trust_env = False
    S2.proxies = {'http': None, 'https': None}
    h = {'User-Agent': 'research-1643', 'Accept-API-Version': 'resource=2.1, protocol=1.0'}
    h.update(headers)
    S2.headers.update(h)
    try:
        r3 = S2.post(BASE + '/am/json/realms/root/realms/alpha/sessions?_action=getSessionInfo',
                     json={'withCredentials': True}, timeout=12, verify=False)
        print('%-45s -> %d %s' % (desc, r3.status_code, r3.text[:150].replace('\n', ' ')))
    except Exception as e:
        print('%-45s -> ERR %s' % (desc, str(e)[:60]))

# 1. 标准 OpenAM header
try_auth('header iPlanetDirectoryPro', {'iPlanetDirectoryPro': tok})
# 2. 标准 OpenAM cookie
try_auth('cookie iPlanetDirectoryPro', {'Cookie': 'iPlanetDirectoryPro=' + tok})
# 3. 抓到的浏览器 cookie 名(自己的新 token 值)
try_auth('cookie aa942d46ece12ce=tokenId', {'Cookie': 'aa942d46ece12ce=' + tok})
# 4. 组合
try_auth('both cookie+header', {'Cookie': 'aa942d46ece12ce=' + tok, 'iPlanetDirectoryPro': tok})
# 5. 其他常见变体
for nm in ['tokenId', 'amTokenId', 'openam.token.id', 'AM_TOKEN_ID', 'sessionToken', 'sid']:
    try_auth('header %s' % nm, {nm: tok})
# 6. resource=1.0 版本下的 header(与登录同版本)
S3 = requests.Session()
S3.trust_env = False
S3.proxies = {'http': None, 'https': None}
S3.headers.update({'User-Agent': 'research-1643', 'Accept-API-Version': 'resource=1.0, protocol=1.0',
                   'iPlanetDirectoryPro': tok})
try:
    r4 = S3.post(BASE + '/am/json/realms/root/realms/alpha/sessions?_action=getSessionInfo',
                 json={'withCredentials': True}, timeout=12, verify=False)
    print('%-45s -> %d %s' % ('header iPlanetDirectoryPro v1.0', r4.status_code, r4.text[:150].replace('\n', ' ')))
except Exception as e:
    print('%-45s -> ERR %s' % ('header iPlanetDirectoryPro v1.0', str(e)[:60]))
